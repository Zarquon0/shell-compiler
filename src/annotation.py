from typing import Self
import abc

# ANNOTATION CLASSES

class Annotation(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __repr__(self) -> str:
        pass

class UniAnnotation(Annotation):
    def __init__(self, target: str, type: str):
        self.target = target.strip()
        self.type = type.strip()
    
    def __repr__(self) -> str:
        return f"<UniAnnotation | type: {self.type}>"

class BiAnnotation(Annotation):
    def __init__(self, target: str, in_type: str = None, out_type: str = None):
        self.target = target.strip()
        self.in_t = in_type.strip()
        self.out_t = out_type.strip()
    
    def __repr__(self) -> str:
        return f"<BiAnnotation | in_type: {self.in_t}, out_type: {self.out_t}>"

    def update(self, update: Self):
        if not self.in_t and update.in_t:
            self.in_t = update.in_t
        elif not self.out_t and update.out_t:
            self.out_t = update.out_t
        else:
            raise Exception(f"Attempted to update BiAnnotation ({self}) with non-mutually exclusive BiAnnotation ({update})")

class StreamAnnotation(BiAnnotation):
    pass

class CommandAnnotation(BiAnnotation):
    pass

class FileAnnotation(UniAnnotation):
    pass

# ANNOTATION TRACKER

class AnnotationTracker:
    def __init__(self):
        self.file_annos: dict[str, FileAnnotation] = {}
        self.clear()
    
    def clear(self):
        self.whole_stream_anno: StreamAnnotation = None
        self.command_annos: dict[str, CommandAnnotation] = {}
    
    def add_annotation(self, anno: Annotation):
        match anno:
            case StreamAnnotation():
                if self.whole_stream_anno:
                   self.whole_stream_anno.update(anno)
                else:
                    self.whole_stream_anno = anno
            case CommandAnnotation():
                if self.command_annos[anno.target]:
                    self.command_annos[anno.target].update(anno)
                else:
                    self.command_annos[anno.target] = anno
            case FileAnnotation():
                if self.file_annos[anno.target]:
                    raise Exception("Attempted to add a file annotation to a file that already has one")
                else:
                    self.file_annos[anno.target] = anno
            case _:
                raise Exception(f"Received unaccounted for annotation type {type(anno)}")