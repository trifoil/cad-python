# cad-python

## first create an environment
```
conda create --name=pyoccenv python=3.10
conda init
conda activate pyoccenv
conda install -c conda-forge pythonocc-core=7.9.0
conda install -c conda-forge numpy
conda install -c conda-forge numpy-stl
conda install -c conda-forge pyqt
export QT_QPA_PLATFORM=wayland

```

## run
```
conda activate pyoccenv
python main.py
```

