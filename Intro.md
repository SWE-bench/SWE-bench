**SWE-bench** is a framework for evaluating AI agents' ability to resolve real-world software issues. It provides an automated "evaluation harness" that takes a codebase and a bug report (issue), lets an AI agent generate a code patch, and then verifies if that patch actually fixes the bug by running tests in a secure, reproducible environment.

### How It Works
The system follows a multi-stage containerized workflow:

1.  **Test Specification (`TestSpec`):** For every task, the system generates a "recipe" that includes the required environment (Python/Java/Kotlin version), installation commands, and the specific test commands that verify the fix.
2.  **Environment Layering:**
    *   **Base Image:** A standard Docker image with core dependencies (defined in `swebench/harness/dockerfiles/`).
    *   **Environment Image:** A layer containing specific language runtimes and pre-installed libraries for a group of repositories.
    *   **Instance Image:** The final layer containing the specific repository at a specific commit, where the AI's patch is applied.
3.  **Execution (`run_evaluation.py`):**
    *   The harness starts a Docker container from the Instance Image.
    *   It applies the AI-generated patch to the code.
    *   It executes the `test_cmd` (defined in `swebench/harness/constants/`) to see if the tests pass or fail.
4.  **Grading & Reporting:**
    *   **Log Parsing:** Tools in `swebench/harness/log_parsers/` extract results from test outputs (e.g., JUnit XMLs for Kotlin).
    *   **Validation:** The system compares the results against "gold" (human-written) solutions to determine if the AI successfully resolved the issue.

### Key Components
*   **`swebench/harness/`**: The core engine that manages Docker containers and runs the evaluation.
*   **`swebench/harness/constants/`**: The knowledge base containing specific build and test instructions for different programming languages (Python, C, Go, and recently expanded Kotlin/Android).
*   **`swebench/collect/`**: Tools for scraping GitHub to create new evaluation tasks from real pull requests.


### Gradle SWE-bench Changes

* `swebench/harness/constants/kotlin.py`
Defines the build and execution specifications for Kotlin-based repositories.

* `swebench/harness/dockerfiles/kotlin.py`
Provides the Dockerfile template used to create the isolated execution environment for Kotlin tasks.

* `analyze_build_failures.py`
A utility script used to parse and categorize errors from build logs.

* `candidates_swe_bench.json`
A dataset of potential SWE-bench task instances (repos, issues, and patches).

### Running the Evaluation (better on linux machine):
```shell
/bin/bash run_evaluation.sh
```

### Further Reading (Usage)
* [Quickstart Guide](docs/guides/quickstart.md): Get started with SWE-bench.
* [Evaluation Tutorial](docs/guides/evaluation.md): Learn how to evaluate models.
* [Inference Guide](docs/reference/inference.md): Run inference on existing models.
