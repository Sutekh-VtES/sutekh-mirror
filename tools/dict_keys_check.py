
"""Custom checker for pylint - warn about about 'in Dict.keys()' usage"""

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker
import re

# pylint: disable-msg=R0904
# Handling three cases, so we exceed the 20 method pylint limit
class MyDictKeyChecker(BaseChecker):
    """Check for "for a in Dict.keys()" usage"""
    
    __implements__ = IASTNGChecker

    name = 'custom_dict_keys'
    msgs = {'W9967': ('Used x in Dict.keys()',
                      ('Used when "x in Dict.keys()" is used rtaher than'
                          ' "x in Dict"')),
            }
    options = ()

    oRegexp = re.compile(' [A-Za-z]* in d.*\.keys()')

    def __internal_test(self, oNode):
        """Grunt work of the test"""
        if hasattr(oNode.list, 'node') and \
                hasattr(oNode.list.node, 'attrname') and \
                oNode.list.node.attrname == 'keys':
            self.add_message('W9967', line=oNode.lineno)

    def visit_for(self, oNode):
        "Check for loops"
        self.__internal_test(oNode)

    def visit_listcompfor(self, oNode):
        "Check [x for x in d] list comprehensions"
        self.__internal_test(oNode)

    def visit_genexpfor(self, oNode):
        "Check (x for x in d) generator expressions"
        self.__internal_test(oNode)

    # Uncomment for testing
    #def __dummy(self, dDict):
    #    """Dummy method used for testing"""
    #    for oYY in dDict.keys():
    #        print oYY
    #    self.oZZ = [oX for oX in dDict.keys()]

def register(oLinter):
    """required method to auto register this checker"""
    oLinter.register_checker(MyDictKeyChecker(oLinter))
        
