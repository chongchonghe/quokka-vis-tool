sc = yt.create_scene(ds, lens_type="perspective")

source = sc[0]

source.set_field(("gas", "density"))
source.set_log(True)

bounds = (3e-31, 5e-27)

# Since this rendering is done in log space, the transfer function needs
# to be specified in log space.
tf = yt.ColorTransferFunction(np.log10(bounds))


def linramp(vals, minval, maxval):
    return (vals - vals.min()) / (vals.max() - vals.min())


tf.map_to_colormap(
    np.log10(3e-31), np.log10(5e-27), colormap="cmyt.arbre", scale_func=linramp
)

source.tfh.tf = tf
source.tfh.bounds = bounds

source.tfh.plot("transfer_function.png", profile_field=("gas", "density"))

sc.save("rendering.png", sigma_clip=6)








import yt

ds = yt.load("Enzo_64/DD0043/data0043")

sc = yt.create_scene(ds, lens_type="perspective")

source = sc[0]

# Set transfer function properties
source.tfh.set_bounds((3e-31, 5e-27))
source.tfh.set_log(True)
source.tfh.grey_opacity = False

source.tfh.plot("transfer_function.png", profile_field=("gas", "density"))

sc.save("rendering.png", sigma_clip=4.0)