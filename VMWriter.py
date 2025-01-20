import typing


class VMWriter:
    """
    Writes VM commands into a file.
    """

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Creates a new file and prepares it for writing VM commands."""
        self.output_stream = output_stream

    def write_to_file(self, command):
        self.output_stream.write(command + '\n')

    def write_push(self, segment: str, index: int) -> None:
        """Writes a VM push command."""
        self.write_to_file(f"push {segment} {index}")

    def write_pop(self, segment: str, index: int) -> None:
        """Writes a VM pop command."""
        self.write_to_file(f"pop {segment} {index}")

    def write_arithmetic(self, command: str) -> None:
        """Writes a VM arithmetic command."""
        self.write_to_file(command)

    def write_label(self, label: str) -> None:
        """Writes a VM label command."""
        self.write_to_file(f"label {label}")

    def write_goto(self, label: str) -> None:
        """Writes a VM goto command."""
        self.write_to_file(f"goto {label}")

    def write_if(self, label: str) -> None:
        """Writes a VM if-goto command."""
        self.write_to_file(f"if-goto {label}")

    def write_call(self, name: str, n_args: int) -> None:
        """Writes a VM call command."""
        self.write_to_file(f"call {name} {n_args}")

    def write_function(self, name: str, n_locals: int) -> None:
        """Writes a VM function command."""
        self.write_to_file(f"function {name} {n_locals}")

    def write_return(self) -> None:
        """Writes a VM return command."""
        self.write_to_file("return")
