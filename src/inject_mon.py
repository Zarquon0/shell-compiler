from shasta.ast_node import *
from collections.abc import Callable
from abc import ABCMeta
from typing import TypeVar
from functools import reduce
from astify import parse_shell_to_asts
import sys
from enum import Enum
from annotation import *
from copy import deepcopy

# MONITOR INJECTION AND HELPERS

MONITOR_BINARY: str = "monitor-components/monitor"

def parse_word_to_argchars(string: str) -> list[CArgChar]:
    return list(map(lambda char: CArgChar(ord(char)), string.strip()))

def parse_word_from_argchars(argchars: list[CArgChar]):
    return " ".join(map(lambda char: char.format(), argchars))

def parse_to_argchars(string: str) -> list[list[CArgChar]]:
    return list(map(lambda word: parse_word_to_argchars(word), string.split(" ")))

def make_mon_command(dfa_path: str, lineno: int) -> CommandNode:
    """Construct a CommandNode for monitor invocation to be added to a pipeline"""
    command_as_str = f"./{MONITOR_BINARY} -d {dfa_path}"
    arg_chars = parse_to_argchars(command_as_str)
    return CommandNode(lineno, [], arg_chars, [])

def inject_monitor(pipe: PipeNode, after_member: int, dfa_path: str):
    """Injects a monitor into the input pipe after the member at index after_member"""
    #Identify pipeline member to monitor
    assert after_member in range(len(pipe.items)), "Specified monitor injection location invalid - member index out of range"
    target_member = pipe.items[after_member]
    #Create proper monitor command
    lineno = find_command_type_and(target_member, CommandNode, lambda cmd_node: cmd_node.line_number)[-1] # MIGHT NEED TO BE MORE RIGOROUS LATER
    mon_command = make_mon_command(dfa_path, lineno)
    #Add monitor command to pipeline
    pipe.items.insert(after_member + 1, mon_command)

T = TypeVar('T')
#U = TypeVar('U')
def find_command_type_and(cmd: Command, target_type: ABCMeta, handler: Callable[[ABCMeta], T]) -> list[T]:
    """
    Highly abstracted Command traversal function. Given a command to start with and a target type, traverses
    through each nested subcommand, finding all subcommands that match the target type, calling a specified
    handler on them, and then returning a list of accumulated results.
    """
    if isinstance(cmd, target_type):
        return [handler(cmd)]
    else:
        next = lambda next_cmds: reduce(lambda results, cmd: results + find_command_type_and(cmd, handler), next_cmds, [])
        match cmd:
            case PipeNode(): 
                return next(cmd.items)
            case CommandNode() | CaseNode(): 
                return []
            case AndNode() | OrNode() | SemiNode():
                return next([cmd.left_operand, cmd.right_operand])
            case SubshellNode() | NotNode() | DefunNode() | ForNode():
                return next([cmd.body])
            case RedirNode() | BackgroundNode():
                return next([cmd.node])
            case IfNode():
                return next([cmd.cond, cmd.then_b, cmd.else_b])
            case WhileNode():
                return next([cmd.test, cmd.body])
            case _:
                print(f"Node encountered of type {type(cmd)}, which was not accounted for")
                return []

# MAIN COMPILING/TRAVERSING

def find_pipelines_and(cmd: Command, pipeline_handle: Callable[[PipeNode], None]):
    def next(next_cmds: list[Command]):
        for cmd in next_cmds:
            find_pipelines_and(cmd, pipeline_handle)
    match cmd:
        case PipeNode(): #Target Node
            pipeline_handle(cmd)
        case CommandNode() | CaseNode(): 
            pass #Dead End - there are no more nested commands
        case AndNode() | OrNode() | SemiNode():
            next([cmd.left_operand, cmd.right_operand])
        case SubshellNode() | NotNode() | DefunNode() | ForNode():
            next([cmd.body])
        case RedirNode() | BackgroundNode():
            next([cmd.node])
        case IfNode():
            next([cmd.cond, cmd.then_b, cmd.else_b])
        case WhileNode():
            next([cmd.test, cmd.body])
        case _:
            print(f"Node encountered of type {type(cmd)}, which was not accounted for")
        
        
    # if isinstance(ast_node, shnodes.CommandNode):
    #     global total_commands
    #     total_commands += 1
    #     print(f"COMMAND {total_commands} FOUND:", ast_node.pretty())
    # else :
    #     for prop in ast_node.__dict__.values():
    #         if isinstance(prop, list):
    #             for el in prop:
    #                 if isinstance(el, shnodes.AstNode):
    #                     traverse_to_commands(el)
    #         elif isinstance(prop, shnodes.AstNode):
    #             traverse_to_commands(prop)
    
def reconstruct_node(cmd: Command) -> str:
    return cmd.pretty()

def transpile(script: list[Command]):
    anno_idcs = []
    anno_tracker = AnnotationTracker()
    for idx, cmd in enumerate(script):
        if anno_check(cmd, anno_tracker):
            anno_idcs.append(idx)
            continue
        pipe_check(cmd, anno_tracker)
    for idx in anno_idcs:
        del script[idx]

ANNOTATION_ARGCHARS = parse_word_to_argchars("annotation")
class AnnotationType(Enum):
    ASSUME = parse_word_to_argchars("assume")
    ASSERT = parse_word_to_argchars("assert")
    EXPECT = parse_word_to_argchars("expect")
    INPUT = parse_word_to_argchars("input")
    OUTPUT = parse_word_to_argchars("output")
    FILE = parse_word_to_argchars("file")
def anno_check(cmd: Command, anno_tracker: AnnotationTracker) -> bool:
    if isinstance(cmd, CommandNode) and cmd.arguments[0] and cmd.arguments[0] == ANNOTATION_ARGCHARS:
        assert cmd.arguments[1] and cmd.arguments[2], "No annotation type provided or incomplete annotation"
        annotation_type = parse_word_from_argchars(cmd.assignments[1])
        match annotation_type:
            case AnnotationType.ASSUME.value | AnnotationType.ASSERT.value | AnnotationType.EXPECT.value | AnnotationType.FILE.value:
                assert cmd.arguments[3], "Incomplete annotation"
                target = parse_word_from_argchars(cmd.arguments[2])
                type = parse_word_from_argchars(cmd.arguments[3])
                match annotation_type:
                    case AnnotationType.ASSUME.value | AnnotationType.ASSERT.value:
                        anno_tracker.add_annotation(CommandAnnotation(target, out_type=type))
                    case AnnotationType.EXPECT.value:
                        anno_tracker.add_annotation(CommandAnnotation(target, in_type=type))
                    case AnnotationType.FILE.value:
                        anno_tracker.add_annotation(FileAnnotation(target, type))
            case AnnotationType.INPUT.value | AnnotationType.OUTPUT.value:
                type = parse_word_from_argchars(cmd.arguments[2])
                match annotation_type:
                    case AnnotationType.INPUT.value:
                        anno_tracker.add_annotation(StreamAnnotation("self", in_type=type))
                    case AnnotationType.OUTPUT.value:
                        anno_tracker.add_annotation(StreamAnnotation("self", out_type=type))
            case _:
                raise Exception(f"Provided annotation type ({annotation_type}) invalid")
        return True
    else:
        return False  

def pipe_check(cmd: Command, anno_tracker: AnnotationTracker):
    if isinstance(cmd, PipeNode):
        monitor_mapping = get_dfas1(cmd, deepcopy(anno_tracker))
        tot_inserted = 0
        for member_idx, dfa_path in monitor_mapping.items():
            inject_monitor(cmd, member_idx + tot_inserted, dfa_path)
            tot_inserted += 1
        anno_tracker.clear()

# STUBS

def get_dfas1(pipe: PipeNode, annotation: AnnotationTracker) -> dict[int, str]:
    pass

def get_dfas(pipe: PipeNode, annotations: list[Annotation]) -> dict[int, str]:
    """Given a pipeline and a list of relevant annotations, returns a mapping of indices within the pipe to
    monitor to paths of serialized DFAs to monitor them with"""
    return mon_all(pipe) #For now...

# DUMMIES

MATCH_ALL_DFA = "monitor-components/sdfa-aaaca133.bc"
def mon_all(pipe: PipeNode) -> dict[int, str]:
    return { idx: MATCH_ALL_DFA for idx in range(len(pipe.items)) }

def inject_all(pipe: PipeNode):
    monitor_mapping = get_dfas(pipe, [])
    tot_inserted = 0
    for member_idx, dfa_path in monitor_mapping.items():
        inject_monitor(pipe, member_idx + tot_inserted, dfa_path)
        tot_inserted += 1

# MAIN BEHAVIOR

if __name__ == "__main__":
    if len(sys.argv) == 2:
        nodes = parse_shell_to_asts(sys.argv[1])
        new_nodes = []
        for node, _text, _start, _end in nodes:
            if not isinstance(node, Command):
                raise Exception(f"Encountered non-Command node of type {type(node)}")
            find_pipelines_and(node, inject_all)
            new_nodes.append(reconstruct_node(node))

        with open("new_script.bash", "w") as f:
            f.write("\n".join(new_nodes) + "\n")
        
    else:
        print("Please provide a shell script to parse")