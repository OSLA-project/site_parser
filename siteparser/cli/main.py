from cloup import command, argument, option
from siteparser.parser import SiteParser


@command(no_args_is_help=True)
@argument("file", required=True, help="The JSON specification to load.")
@option(
    "-o",
    "--output",
    default=None,
    help="File to save the generated graph to.",
)
@option(
    "-s",
    "--summarise",
    is_flag=True,
    default=False,
    help="Print a summary of the devices found.",
)
@option(
    "-v",
    "--visualise",
    is_flag=True,
    default=False,
    help="Visualise the graph.",
)
def main(
    file: str,
    output: str | None = None,
    summarise: bool = False,
    visualise: bool = False,
):
    parser = SiteParser(file)

    if summarise:
        parser.summarise()

    parser.make_graph(output, visualise)
