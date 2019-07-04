import gi
import signal
from . import appindicator_utils, client_smi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')

from gi.repository import GObject

client_smi.parser.add_argument('--min-mem-notif', '-n', default=200, help='min memory usage to trigger Notification')


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    GObject.threads_init()
    appindicator_utils.main()


if __name__ == "__main__":
    main()
