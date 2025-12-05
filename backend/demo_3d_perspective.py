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