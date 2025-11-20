import subprocess


def get_namespace_status(namespace: str) -> str:
    """
    Fragt den Status der Pods in einem Namespace ab.
    Gibt einen einfachen Text zurück: "Running", "Pending", "Failed", "No pods" oder "Unknown".
    """
    try:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "pods",
                "-n",
                namespace,
                "-o",
                "jsonpath={.items[*].status.phase}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()
        if not output:
            return "No pods"

        phases = output.split()  # z.B. ["Running", "Running"]
        if all(p == "Running" for p in phases):
            return "Running"
        if any(p == "Failed" for p in phases):
            return "Failed"
        if any(p == "Pending" for p in phases):
            return "Pending"
        return "Unknown"

    except subprocess.CalledProcessError as e:
        # z.B. Namespace existiert nicht (mehr)
        return f"Error: {e.stderr.strip() or 'kubectl error'}"
    except Exception as e:
        return f"Error: {str(e)}"
