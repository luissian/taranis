import logging

import click
import os
import rich.console
import rich.logging
import rich.traceback
import sys

import taranis.utils
import taranis.reference_alleles

log = logging.getLogger()

# Set up rich stderr console
stderr = rich.console.Console(
    stderr=True, force_terminal=taranis.utils.rich_force_colors()
)


def run_taranis():
    # Set up the rich traceback
    rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)

    # Print taranis header
    # stderr.print("\n[green]{},--.[grey39]/[green],-.".format(" " * 42), highlight=False)
    stderr.print("[blue]                ______           ___                     ___    ",  highlight=False, )
    stderr.print("[blue]   \    |-[grey39]-|  [blue] |__--__|   /\    |   \    /\    |\   | | |  ", highlight=False,)
    stderr.print("[blue]    \   \  [grey39]/ [blue]     ||     /  \   |__ /   /  \   | \  | | |___   ",   highlight=False,)
    stderr.print("[blue]    /  [grey39] / [blue] \      ||    /____\  |  \   /____\  |  \ | |     |", highlight=False, )
    stderr.print("[blue]   /   [grey39] |-[blue]-|      ||   /      \ |   \ /      \ |   \| |  ___| ",  highlight=False,)

    # stderr.print("[green]                                          `._,._,'\n", highlight=False)
    __version__ = "2.1.0"
    stderr.print(
        "\n" "[grey39]    Taranis version {}".format(__version__), highlight=False
    )

    # Lanch the click cli
    taranis_cli()


# Customise the order of subcommands for --help
class CustomHelpOrder(click.Group):
    def __init__(self, *args, **kwargs):
        self.help_priorities = {}
        super(CustomHelpOrder, self).__init__(*args, **kwargs)

    def get_help(self, ctx):
        self.list_commands = self.list_commands_for_help
        return super(CustomHelpOrder, self).get_help(ctx)

    def list_commands_for_help(self, ctx):
        """reorder the list of commands when listing the help"""
        commands = super(CustomHelpOrder, self).list_commands(ctx)
        return (
            c[1]
            for c in sorted(
                (self.help_priorities.get(command, 1000), command)
                for command in commands
            )
        )

    def command(self, *args, **kwargs):
        """Behaves the same as `click.Group.command()` except capture
        a priority for listing command names in help.
        """
        help_priority = kwargs.pop("help_priority", 1000)
        help_priorities = self.help_priorities

        def decorator(f):
            cmd = super(CustomHelpOrder, self).command(*args, **kwargs)(f)
            help_priorities[cmd.name] = help_priority
            return cmd

        return decorator


@click.group(cls=CustomHelpOrder)
@click.version_option(taranis.__version__)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Print verbose output to the console.",
)
@click.option(
    "-l", "--log-file", help="Save a verbose log to a file.", metavar="<filename>"
)
def taranis_cli(verbose, log_file):
    # Set the base logger to output DEBUG
    log.setLevel(logging.DEBUG)

    # Set up logs to a file if we asked for one
    if log_file:
        log_fh = logging.FileHandler(log_file, encoding="utf-8")
        log_fh.setLevel(logging.DEBUG)
        log_fh.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(name)-20s [%(levelname)-7s]  %(message)s"
            )
        )
        log.addHandler(log_fh)

# Reference alleles
@taranis_cli.command(help_priority=2)
@click.option("-s", "--schema", required=True, multiple=False, type=click.Path(), help="Directory where the schema with the core gene files are located. ")
@click.option("-o", "--output", required=True, multiple=False, type=click.Path(), help="Output folder to save reference alleles")
def reference_alleles(
    schema,
    output,
):
    # taranis reference-alleles -s ../../documentos_antiguos/datos_prueba/schema_test/ -o ../../new_taranis_result_code
    if not taranis.utils.folder_exists(schema):
        log.error("schema folder %s does not exists", schema)
        stderr.print(
            "[red] Schema folder does not exist. " + schema + "!"
        )
        sys.exit(1)
    schema_files = taranis.utils.get_files_in_folder(schema, "fasta")
    if len(schema_files) == 0:
        log.error("Schema folder %s does not have any fasta file", schema)
        stderr.print("[red] Schema folder does not have any fasta file")
        sys.exit(1)
    # Check if output folder exists
    if taranis.utils.folder_exists(output):
        q_question = "Folder " + output + " already exists. Files will be overwritten. Do you want to continue?"
        if "no" in taranis.utils.query_user_yes_no(q_question, "no"):
            log.info("Aborting code by user request")
            stderr.print("[red] Exiting code. ")
            sys.exit(1)
    else:
        try:
            os.makedirs(output)
        except OSError as e:
            log.info("Unable to create folder at %s", output)
            stderr.print("[red] ERROR. Unable to create folder  " + output)
            sys.exit(1)
    """Create the reference alleles from the schema """
    for f_file in schema_files:
        ref_alleles = taranis.reference_alleles.ReferenceAlleles(f_file, output)
    _ = ref_alleles.create_ref_alleles()