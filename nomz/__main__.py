import os
import sys
import traceback
from collections.abc import Iterator

from i3ipc import Con, Connection, Event, WindowEvent  # type: ignore

app_ids: list[str] = []

STAT_PATH = (
    "stat"
    if os.access(f"/proc/{os.getpid()}/stat", os.R_OK)
    # BSD moment
    else "status"
)

swallowed: dict[int, Con] = {}


def traverse_pids(pid: int) -> Iterator[int]:
    while pid:
        yield pid
        with open(f"/proc/{pid}/{STAT_PATH}", "rb") as f:
            pid = int(f.read().split(b" ")[3])


def cmd(con: Con, cmd: str) -> None:
    for reply in con.command(cmd):
        if not reply.success:
            raise RuntimeError(reply.error)


def swallow(parent: Con, child: Con) -> None:
    print(child.app_id, "nomz", parent.app_id)
    rect = parent.geometry
    # basically just swap and throw the window out of bounds
    cmd(child, f"swap container with con_id {parent.id}")
    cmd(parent, f"mark --add _nomz_{parent.id}")
    cmd(parent, "floating enable")
    cmd(parent, f"move position {-rect.width * 2} px {-rect.height * 2} px")
    swallowed[child.id] = parent


def unswallow(ipc: Connection, parent: Con, child: Con) -> None:
    print(child.app_id, "unnomz", parent.app_id)
    cmd(parent, "floating disable")
    cmd(parent, f"move container to mark _nomz_{parent.id}")
    cmd(parent, "focus")
    del swallowed[child.id]


def on_new_window(ipc: Connection, event: WindowEvent) -> None:
    if event.container.app_id in app_ids:
        return

    tree = ipc.get_tree()
    parent_con: Con = tree.find_by_id(event.container.id).parent
    for pid in traverse_pids(event.container.pid):
        if cons := parent_con.find_by_pid(pid):
            if cons[0].app_id in app_ids:
                try:
                    swallow(cons[0], event.container)
                except Exception:
                    print("Failed to swallow window:", sys.stderr)
                    traceback.print_exc()
                return


def on_window_close(ipc: Connection, event: WindowEvent) -> None:
    if parent := swallowed.get(event.container.id):
        try:
            unswallow(ipc, parent, event.container)
        except Exception:
            print("Failed to unswallow window:", file=sys.stderr)
            traceback.print_exc()


def main() -> None:
    app_ids.extend(sys.argv[1:])
    ipc = Connection()
    ipc.on(Event.WINDOW_NEW, on_new_window)
    ipc.on(Event.WINDOW_CLOSE, on_window_close)
    ipc.main()


if __name__ == "__main__":
    main()
