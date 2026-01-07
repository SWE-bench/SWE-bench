import subprocess
import sys
import argparse

def exec_to_file(command: str, log_file: str) -> int:
    """
    Execute a command and redirect all output to a file using subshell redirection.
    This preserves internal pipe safety while capturing interleaved stdout/stderr.
    Passes command via stdin to avoid ARG_MAX limits for large commands.
    """
    # Pass command via stdin to shell to avoid ARG_MAX limits
    # Wrap in subshell to capture everything correctly
    full_cmd = f"({command}) > {log_file} 2>&1"
    
    # Use stdin to pass the command, avoiding ARG_MAX limits
    process = subprocess.Popen(
        ["/bin/bash"],
        stdin=subprocess.PIPE,
        text=True
    )
    process.communicate(full_cmd)
    return process.returncode

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, help="The command to execute (use '-' to read from stdin)")
    parser.add_argument("log_file", type=str)
    args = parser.parse_args()
    
    command = args.command
    if command == "-":
        command = sys.stdin.read()
    
    sys.exit(exec_to_file(command, args.log_file))
