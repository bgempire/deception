"""Framework initialization. Reference: https://bgempire.github.io/bgforce/structure """

from . import bgf

from .map import loader as mapLoader

# Load map
mapLoader.load()