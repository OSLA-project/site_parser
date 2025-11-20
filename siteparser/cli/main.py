from cloup import command, argument, option
from siteparser.parser import SiteParser


@command(no_args_is_help=True)
@argument("file", required=True, help="The JSON specification to load.")
@option(
    "-s",
    "--summarise",
    is_flag=True,
    default=False,
    help="Print a summary of the devices found.",
)
@option(
    "-o",
    "--output",
    default=None,
    help="File to save the generated graph to.",
)
@option(
    "-v",
    "--visualise",
    default=None,
    help="Visualise the graph.",
)
def main(
    file: str,
    summarise: bool,
    output: str | None = None,
    visualise: str | None = None,
):
    parser = SiteParser(file)

    if summarise:
        parser.summarise()

    parser.make_graph(output, visualise)
