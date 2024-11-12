from aisync.decorators import graph


@graph
def main():
    return """
graph TD
    START --> A
    A --> gpt35
    A --> gpt4omini
    gpt35 --> king
    gpt4omini --> king
    king --> END
    """
