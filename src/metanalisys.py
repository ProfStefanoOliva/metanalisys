import sys

from metanalisys_core import OFFICE_FORMATS
from metanalisys_core import FileAccessError
from metanalisys_core import InvalidOfficeFileError
from metanalisys_core import UnsupportedFormatError
from metanalisys_core import analyze_office_file
from metanalisys_core import build_report_paths
from metanalisys_core import format_text_report
from metanalisys_core import save_json_report
from metanalisys_core import save_text_report


def choose_output_mode() -> str:
    print("\nOFFICE FORENSIC ANALYZER\n")
    print("Seleziona modalità output:\n")
    print("1 - Stampa su schermo")
    print("2 - Salvataggio su file TXT\n")
    output_mode = input("Scelta: ").strip()
    if output_mode not in {"1", "2"}:
        print("\n[ERRORE]")
        print("Modalità non valida.")
        raise SystemExit(1)
    return output_mode


def choose_file_path() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    return input("\nInserisci il percorso completo del file Office:\n> ").strip().strip('"')


def print_supported_formats() -> None:
    print("\nFormati riconosciuti:")
    for extension, spec in sorted(OFFICE_FORMATS.items()):
        print(f"- {extension}: {spec.label} [{spec.metadata_support}]")


def main() -> int:
    output_mode = choose_output_mode()
    office_file = choose_file_path()
    try:
        results = analyze_office_file(office_file)
        report_text = format_text_report(results)
        report_paths = build_report_paths(office_file)

        if output_mode == "1":
            print("\n")
            print(report_text)
        else:
            save_text_report(report_text, report_paths["txt"])
            print(f"\nReport TXT salvato in: {report_paths['txt']}")

        save_json_report(results, report_paths["json"])
        print(f"Report JSON salvato in: {report_paths['json']}")
        return 0
    except UnsupportedFormatError as exc:
        print("\n[ERRORE]")
        print(f"Formato non supportato: {exc}")
        print_supported_formats()
        return 1
    except FileAccessError as exc:
        print("\n[ERRORE]")
        print(str(exc))
        return 1
    except InvalidOfficeFileError as exc:
        print("\n[ERRORE]")
        print(str(exc))
        return 1
    except Exception as exc:
        print("\n[ERRORE DURANTE L'ANALISI]")
        print(type(exc).__name__)
        print(str(exc))
        return 1


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    sys.exit(main())
