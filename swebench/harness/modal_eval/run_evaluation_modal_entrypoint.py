import subprocess
import sys
import argparse

def exec_to_file(command: str, log_file: str) -> int:
    """
    Execute a command and redirect all output to a file using subshell redirection.
    This preserves internal pipe safety while capturing interleaved stdout/stderr.
    """
    # Wrap in subshell to capture everything correctly
    full_cmd = f"({command}) > {log_file} 2>&1"
    
    process = subprocess.Popen(full_cmd, shell=True)
    process.wait()
    return process.returncode

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str)
    parser.add_argument("log_file", type=str)
    args = parser.parse_args()
    
    sys.exit(exec_to_file(args.command, args.log_file))
