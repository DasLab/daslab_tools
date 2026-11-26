#!/usr/bin/env python3
"""Align two scans of the same gel and merge them into a false-colour overlay.

Typical use: a FAM scan and a SYBR Gold scan of one gel. Because the gel is
usually taken off the platen and re-placed between the two scans (e.g. to stain
it), the two images differ by a rigid move -- a shift of tens of pixels plus a
fraction of a degree of rotation. Band content differs completely between the
channels, so ordinary cross-correlation fails; this uses Mattes mutual
information, the standard metric for multi-modal registration, via SimpleITK.

Works on raw 16-bit Typhoon .gel/.tif scans and on 8-bit PNG screenshots alike;
band polarity is auto-detected. Registering the full .gel frames is more robust
than registering tight crops, because the gel outline and well comb are the
features the two channels actually share.

    pip install SimpleITK

    python3 merge_gel_channels.py --ref SYBR.png --mov FAM.png --out merged.png

Reference stays fixed; moving is resampled onto it, so the output is in the
reference's frame at the reference's size.
"""

import argparse
import numpy as np
from PIL import Image
import SimpleITK as sitk


COLOURS = {"red": (1, 0, 0), "green": (0, 1, 0), "blue": (0, 0, 1),
           "cyan": (0, 1, 1), "magenta": (1, 0, 1), "yellow": (1, 1, 0),
           "white": (1, 1, 1)}


def load_signal(path, polarity="auto", bg_pct=2.0, peak_pct=99.9):
    """Return (signal in 0..1 where 1 is a strong band, detected polarity)."""
    im = Image.open(path)
    if im.mode in ("I;16", "I;16B", "I;16L", "I", "F"):
        grey = np.asarray(im).astype(np.float32)
    else:
        grey = np.asarray(im.convert("L"), dtype=np.float32)

    if polarity == "auto":
        lo, hi = np.percentile(grey, [1, 99])
        mid = np.median(grey)
        polarity = "light" if (mid - lo) < (hi - mid) else "dark"

    if polarity == "light":          # bands brighter than background (raw scan)
        sig = grey - np.percentile(grey, bg_pct)
    else:                            # bands darker (inverted-greyscale figure)
        sig = np.percentile(grey, 100.0 - bg_pct) - grey

    sig = np.clip(sig, 0.0, None)
    peak = np.percentile(sig, peak_pct)
    return (sig / peak if peak > 0 else sig), polarity


def make_transform(shift_xy, angle_deg, ref_shape, allow_scale=False, scale=1.0):
    """Rigid (or similarity) transform from an explicit shift (px, positive =
    right/down) and rotation. Pass allow_scale=True so a seeded run can still
    fit scale -- a Euler2D seed silently locks scale at 1."""
    t = sitk.Similarity2DTransform() if allow_scale else sitk.Euler2DTransform()
    if allow_scale:
        t.SetScale(scale)
    t.SetCenter([ref_shape[1] / 2.0, ref_shape[0] / 2.0])
    t.SetAngle(np.deg2rad(angle_deg))
    t.SetTranslation([-shift_xy[0], -shift_xy[1]])
    return t


def register(ref, mov, allow_scale=False, iterations=1000, verbose=True, init=None,
             affine=False):
    """Fit moving onto reference. Returns the SimpleITK transform.

    affine=True adds a second stage with a full 2D affine (anisotropic scale +
    shear), seeded from the similarity fit. A gel that is soaked between the two
    scans swells, and it does not swell rigidly -- x and y stretch by different
    amounts -- so similarity can leave a residual that grows across the gel."""
    fixed = sitk.GetImageFromArray(ref.astype(np.float32))
    moving = sitk.GetImageFromArray(mov.astype(np.float32))
    if affine:
        sim = register(ref, mov, allow_scale=True, verbose=verbose, init=init)
        # R.Execute hands back a CompositeTransform; unwrap to the Similarity2D
        inner = sim
        if hasattr(inner, "GetNumberOfTransforms"):
            inner = inner.GetNthTransform(inner.GetNumberOfTransforms() - 1)
        inner = sitk.Similarity2DTransform(inner)
        base = sitk.AffineTransform(2)
        base.SetCenter(inner.GetCenter())
        base.SetMatrix(inner.GetMatrix())
        base.SetTranslation(inner.GetTranslation())
        init = base
        if verbose:
            print("  refining with a full affine:")
    base = (sitk.AffineTransform(2) if affine else
            sitk.Similarity2DTransform() if allow_scale else sitk.Euler2DTransform())
    if init is None:
        init = sitk.CenteredTransformInitializer(
            fixed, moving, base, sitk.CenteredTransformInitializerFilter.GEOMETRY)

    R = sitk.ImageRegistrationMethod()
    R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=64)
    R.SetMetricSamplingStrategy(R.NONE)   # all pixels: deterministic
    R.SetInterpolator(sitk.sitkLinear)
    R.SetOptimizerAsRegularStepGradientDescent(
        learningRate=2.0, minStep=1e-6, numberOfIterations=iterations,
        gradientMagnitudeTolerance=1e-8)
    R.SetOptimizerScalesFromPhysicalShift()
    # coarse-to-fine, so a shift of ~100 px is still found
    R.SetShrinkFactorsPerLevel([8, 4, 2, 1])
    R.SetSmoothingSigmasPerLevel([4, 2, 1, 0])
    R.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    R.SetInitialTransform(init, inPlace=False)

    out = R.Execute(fixed, moving)
    if verbose:
        p = out.GetParameters()
        if len(p) == 6:                      # Affine: matrix 2x2 then tx, ty
            m = np.array(p[:4]).reshape(2, 2)
            sx, sy = np.linalg.norm(m[:, 0]), np.linalg.norm(m[:, 1])
            shear = np.rad2deg(np.arcsin(np.clip(np.dot(m[:, 0], m[:, 1]) /
                                                 (sx * sy), -1, 1)))
            ang = np.rad2deg(np.arctan2(m[1, 0], m[0, 0]))
            print(f"  scale x {sx:.4f} y {sy:.4f}   rotation {ang:+.3f} deg   "
                  f"shear {shear:+.3f} deg   shift ({p[4]:+.1f}, {p[5]:+.1f}) px")
        else:
            if len(p) == 4:                  # Similarity2D: scale, angle, tx, ty
                scale, angle, tx, ty = p
            else:                            # Euler2D: angle, tx, ty
                scale, (angle, tx, ty) = 1.0, p
            print(f"  scale {scale:.4f}   rotation {np.rad2deg(angle):+.3f} deg   "
                  f"shift ({tx:+.1f}, {ty:+.1f}) px")
        print(f"  mutual information {R.GetMetricValue():.4f}   "
              f"({R.GetOptimizerStopConditionDescription()})")
    return out


def resample(mov, transform, ref_shape):
    fixed = sitk.GetImageFromArray(np.zeros(ref_shape, dtype=np.float32))
    moving = sitk.GetImageFromArray(mov.astype(np.float32))
    out = sitk.Resample(moving, fixed, transform, sitk.sitkLinear, 0.0,
                        moving.GetPixelID())
    return np.clip(sitk.GetArrayFromImage(out), 0, None)


def colourise(ref_sig, mov_sig, ref_colour, mov_colour, white_bg, gamma, gain):
    def shape(s):
        return np.clip(np.clip(s, 0, 1) ** gamma * gain, 0, 1)

    a, b = shape(ref_sig), shape(mov_sig)
    rgb = np.zeros(a.shape + (3,), dtype=np.float32)
    for i in range(3):
        if white_bg:   # subtractive: each channel removes its complement
            rgb[..., i] = 1.0 - (a * (1 - ref_colour[i]) + b * (1 - mov_colour[i]))
        else:          # additive on black; overlap blends
            rgb[..., i] = a * ref_colour[i] + b * mov_colour[i]
    return (np.clip(rgb, 0, 1) * 255).astype(np.uint8)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ref", required=True, help="reference scan (stays fixed)")
    p.add_argument("--mov", required=True, help="moving scan (aligned to --ref)")
    p.add_argument("--out", required=True, help="output PNG")
    p.add_argument("--ref-colour", default="red", choices=sorted(COLOURS))
    p.add_argument("--mov-colour", default="blue", choices=sorted(COLOURS))
    p.add_argument("--polarity", default="auto", choices=["auto", "light", "dark"],
                   help="are bands brighter or darker than background")
    p.add_argument("--bg-pct", type=float, default=2.0,
                   help="percentile treated as background; raise it (60-80) on raw "
                        ".gel scans to subtract gel autofluorescence")
    p.add_argument("--shift", metavar="DX,DY",
                   help="move the moving image by DX,DY px (positive = right, down). "
                        "Used as the starting guess, or as the final answer with --manual.")
    p.add_argument("--rotate", type=float, default=0.0,
                   help="rotation in degrees to pair with --shift")
    p.add_argument("--manual", action="store_true",
                   help="skip fitting; use --shift/--rotate exactly. Use when the fit "
                        "is under-determined (e.g. few bands shared between channels).")
    p.add_argument("--allow-scale", action="store_true",
                   help="fit scale too; leave off unless the zoom really differed")
    p.add_argument("--affine", action="store_true",
                   help="fit a full affine (anisotropic scale + shear) after the "
                        "similarity fit. Use when the gel was soaked between scans "
                        "and swelled unevenly, so lanes drift apart across the gel")
    p.add_argument("--white-bg", action="store_true",
                   help="subtractive merge on white, for printing")
    p.add_argument("--gamma", type=float, default=1.0, help="<1 lifts faint bands")
    p.add_argument("--gain", type=float, default=1.0)
    p.add_argument("--crop", metavar="X0,Y0,X1,Y1",
                   help="crop the output to this box, in reference pixels")
    p.add_argument("--crop-overlap", action="store_true",
                   help="crop to the region both images cover")
    p.add_argument("--landmarks", metavar="FILE",
                   help="fit the transform from corresponding points instead of image "
                        "content. FILE has one pair per line: movx movy refx refy "
                        "(blank lines and # comments ignored). Fits a similarity, or a "
                        "full affine with --affine. This is the reliable route when the "
                        "channels share too few bands for mutual information, or when "
                        "you already know which bands correspond")
    p.add_argument("--map", metavar="SX,TX,SY,TY",
                   help="skip fitting and use an explicit axis-aligned affine measured "
                        "from the images: ref_x = SX*mov_x + TX, ref_y = SY*mov_y + TY. "
                        "Use when mutual information under-fits the stretch: MI is "
                        "dominated by the gel outline, so it can leave a 1-2%% scale "
                        "error that shows up as lanes drifting apart across the gel. "
                        "Measure SX,TX by cross-correlating the two lane combs over "
                        "scale and offset, and SY,TY from landmark bands")
    p.add_argument("--post-shift", metavar="DX,DY",
                   help="translate the aligned moving image by DX,DY px afterwards "
                        "(positive = right/down). Mutual information is computed over "
                        "the whole frame and is weakly constrained in x, so it can sit "
                        "a few px off the lane comb even when scale and rotation are "
                        "right; measure the residual against the lanes and correct it "
                        "here rather than perturbing the fit")
    p.add_argument("--save-aligned", metavar="PNG",
                   help="also write the resampled moving image on its own")
    args = p.parse_args()

    ref_sig, ref_pol = load_signal(args.ref, args.polarity, args.bg_pct)
    mov_sig, mov_pol = load_signal(args.mov, args.polarity, args.bg_pct)
    print(f"reference {args.ref}\n  {ref_sig.shape[1]}x{ref_sig.shape[0]}, bands {ref_pol}")
    print(f"moving    {args.mov}\n  {mov_sig.shape[1]}x{mov_sig.shape[0]}, bands {mov_pol}")

    print("registering (Mattes mutual information, "
          f"{'similarity' if args.allow_scale else 'rigid'}):" if not args.manual
          else "using the transform given on the command line:")
    shift = [float(v) for v in args.shift.split(",")] if args.shift else None
    if args.affine:
        args.allow_scale = True
    if args.landmarks:
        pts = np.loadtxt(args.landmarks, comments="#")
        mov_p, ref_p = pts[:, :2], pts[:, 2:4]
        if args.affine:
            A = np.hstack([mov_p, np.ones((len(mov_p), 1))])
            sol, *_ = np.linalg.lstsq(A, ref_p, rcond=None)
            M, t = sol[:2, :].T, sol[2, :]
        else:                                    # similarity: scale + rotation
            mc, rc = mov_p.mean(0), ref_p.mean(0)
            m0, r0 = mov_p - mc, ref_p - rc
            den = (m0 ** 2).sum()
            a = (m0[:, 0] * r0[:, 0] + m0[:, 1] * r0[:, 1]).sum() / den
            b = (m0[:, 0] * r0[:, 1] - m0[:, 1] * r0[:, 0]).sum() / den
            M = np.array([[a, -b], [b, a]]); t = rc - M @ mc
        res = [np.hypot(*(M @ m + t - r)) for m, r in zip(mov_p, ref_p)]
        Mi = np.linalg.inv(M)
        tf = sitk.AffineTransform(2)
        tf.SetMatrix(Mi.flatten().tolist())      # ref -> mov
        tf.SetTranslation((-Mi @ t).tolist())
        print(f"  landmarks: {len(pts)} pairs, "
              f"scale x {np.hypot(*M[:,0]):.4f} y {np.hypot(*M[:,1]):.4f}, "
              f"rotation {np.degrees(np.arctan2(M[1,0],M[0,0])):+.2f} deg")
        print("  residuals: " + " ".join(f"{r:.1f}" for r in res) + " px")
    elif args.map:
        sx, tx, sy, ty = (float(v) for v in args.map.split(","))
        tf = sitk.AffineTransform(2)
        tf.SetMatrix([1.0 / sx, 0.0, 0.0, 1.0 / sy])      # ref -> mov is the inverse
        tf.SetTranslation([-tx / sx, -ty / sy])
        print(f"  explicit map: ref_x = {sx:.4f}*mov_x {tx:+.1f}, "
              f"ref_y = {sy:.4f}*mov_y {ty:+.1f}")
    elif args.manual:
        if shift is None:
            p.error("--manual needs --shift")
        tf = make_transform(shift, args.rotate, ref_sig.shape,
                            args.allow_scale)
        print(f"  manual: shift ({shift[0]:+.1f}, {shift[1]:+.1f}) px, "
              f"rotation {args.rotate:+.3f} deg")
    else:
        reg_ref, _ = load_signal(args.ref, args.polarity, 2.0)
        reg_mov, _ = load_signal(args.mov, args.polarity, 2.0)
        seed = (make_transform(shift, args.rotate, ref_sig.shape,
                               args.allow_scale) if shift else None)
        tf = register(reg_ref, reg_mov, args.allow_scale or args.affine,
                      init=seed, affine=args.affine)
    mov_aligned = resample(mov_sig, tf, ref_sig.shape)
    if args.post_shift:
        pdx, pdy = (float(v) for v in args.post_shift.split(","))
        from scipy.ndimage import shift as ndshift
        mov_aligned = ndshift(mov_aligned, (pdy, pdx), order=1,
                              mode="constant", cval=0.0)
        print(f"  post-shift ({pdx:+.1f}, {pdy:+.1f}) px on the moving image")

    if args.crop_overlap:
        cover = resample(np.ones_like(mov_sig), tf, ref_sig.shape) > 0.5
        rows, cols = np.where(cover.any(1))[0], np.where(cover.any(0))[0]
        sl = (slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1))
        ref_sig, mov_aligned = ref_sig[sl], mov_aligned[sl]
        print(f"  cropped to overlap: {ref_sig.shape[1]}x{ref_sig.shape[0]}")

    if args.crop:
        x0, y0, x1, y1 = (int(v) for v in args.crop.split(","))
        ref_sig, mov_aligned = ref_sig[y0:y1, x0:x1], mov_aligned[y0:y1, x0:x1]
        print(f"  cropped to {x1-x0}x{y1-y0} at ({x0},{y0})")

    rgb = colourise(ref_sig, mov_aligned, COLOURS[args.ref_colour],
                    COLOURS[args.mov_colour], args.white_bg, args.gamma, args.gain)
    Image.fromarray(rgb).save(args.out)
    print(f"wrote {args.out}   {args.ref_colour} = ref, {args.mov_colour} = moving")

    if args.save_aligned:
        g = (np.clip(mov_aligned, 0, 1) * 255).astype(np.uint8)
        Image.fromarray(g).save(args.save_aligned)
        print(f"wrote {args.save_aligned}")


if __name__ == "__main__":
    main()
