from shasta.json_to_ast import to_ast_node
import logging
import libdash.parser
import libdash
import shseer.reporter as reporter 
from shseer.error_report import ParseError
from shseer.exceptions import ParseException 
import os
import sys
import traceback
INITIALIZE_LIBDASH = True
## Parses straight a shell script to an AST
## through python without calling it as an executable
def parse_shell_to_asts(input_script_path : str):
    global INITIALIZE_LIBDASH
    try:
        if not os.path.isfile(input_script_path):
            raise libdash.parser.ParsingException(f"File {input_script_path} does not exist")
        logging.debug(f"Calling libdash parser initialization={INITIALIZE_LIBDASH} on {input_script_path}")
        new_ast_objects = libdash.parser.parse(input_script_path,init=INITIALIZE_LIBDASH)
        INITIALIZE_LIBDASH = False
        logging.debug(f"Finished libdash parser on {input_script_path}")
        ## Transform the untyped ast objects to typed ones
        new_ast_objects = list(new_ast_objects)
        logging.debug("Calling shasta")
        typed_ast_objects = []
        for (
            untyped_ast,
            original_text,
            linno_before,
            linno_after,
        ) in new_ast_objects:
            typed_ast = to_ast_node(untyped_ast)
            typed_ast_objects.append(
                (typed_ast, original_text, linno_before, linno_after)
            )
        logging.debug("Returning typed Shasta objects")
        return typed_ast_objects
    except Exception as e:
        logging.debug("Parsing error!", traceback.format_exc())
        parse_error_report = ParseError(str(e))
        reporter.REPORTER.add_parse_error(parse_error_report)
        raise ParseException(str(e))

def parse_shell_to_asts_interactive(input_script_path: str):
    return libdash.parser.parse(input_script_path)

def inject_monitors(input_script_path: str):
    asts = parse_shell_to_asts(input_script_path)
    for node, _text, _start, _end in asts:
        print(node)            # High-level view
        print(vars(node))      # Fields
        print(dir(node))       # Attributes and methods

if __name__=="__main__":
    if len(sys.argv) == 3:
        inject_monitors(sys.argv[2])
    else:
        print("Please provide a shell script to parse")