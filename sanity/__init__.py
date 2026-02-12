# (In)SanityLang Interpreter
# "Every feature is simple. Every feature interacts with every other feature. Good luck."
__version__ = "0.1.0"

from .runtime import Interpreter, SanityError
from .types import SanValue, SanType
from .sanity_points import SanityTracker
import sanity.runtime_statements  # Install statement executors
