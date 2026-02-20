"""Entry point for python -m preprocessing"""
import sys
sys.path.insert(0, '/app/glintstone/src')
from preprocessing.cli import main
sys.exit(main())
