# import sys
# from astify import parse_shell_to_asts

# if __name__ == "__main__":
#     if len(sys.argv) == 2:
#         nodes = parse_shell_to_asts(sys.argv[1])
#         new_nodes = []
#         for node, _text, _start, _end in nodes:
#             if not isinstance(node, Command):
#                 raise Exception(f"Encountered non-Command node of type {type(node)}")
#             find_pipelines_and(node, inject_all)
#             new_nodes.append(reconstruct_node(node))

#         with open("new_script.bash", "w") as f:
#             f.write("\n".join(new_nodes) + "\n")
        
#     else:
#         print("Please provide a shell script to parse")