# this script exists in order to work around pip issues with customizing the 
# GDAL package's installation

# TODO
# Create a more general installation script that also includes the other
# requirements

# symlink gdal-config to the virtualenv's bin directory
GDAL_CONFIG=$(which gdal-config)
ln -s ${GDAL_CONFIG} python/bin/gdal-config

# get the special variables from gdal-config
MINVERSION=$(gdal-config --version | sed "s_\(\w\.\w\).*_\1_g")
MAXVERSION=$(echo "$MINVERSION+0.1" | bc)
LIBDIR=$(gdal-config --libs | sed "s_-L\(.*\) .*_\1_g")
LIBNAME=$(gdal-config --libs | sed "s_.*-l\(.*\)_\1_g")

# download the package with pip
pip install --no-install "GDAL>=$MINVERSION, <$MAXVERSION"

# modify setup-py
cd python/build/GDAL
python setup.py build_ext --gdal-config=$GDAL_CONFIG --library-dirs=$LIBDIR \
	--libraries=$LIBNAME --include-dirs=/usr/include/gdal
cd -

# install the package with pip
pip install --no-download GDAL
