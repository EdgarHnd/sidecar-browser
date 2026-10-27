# Interaction targets

Much of Arc's feel comes from small motions: things fade instead of popping,
dragged items lift and push their neighbours aside, and drops snap into place.
This list tracks those details for Sidecar. Durations are starting values to be
tuned by eye with Arc side by side; they are not taken from Arc's code or
assets, and no Arc code, icons, or artwork are used.

| Interaction | Target behaviour | Sidecar before | Status |
|---|---|---|---|
| Favorite hover | Background fades in and out (~120 ms) | Instant swap | Implemented |
| Favorite press | Tile shrinks slightly while held and springs back | None | Implemented |
| Reorder Favorites by dragging | Tile lifts and follows the pointer; neighbours slide aside live (~180 ms ease-out); release snaps it into the slot; Escape or lost capture returns it | macOS drag session; tiles only highlighted; grid rebuilt on drop | Implemented |
| Reorder, add, or remove from menus | Tiles slide to their new slots | Grid rebuilt instantly | Implemented |
| Cmd+T bar appears | Fades in (~120 ms) | Pops in | Implemented |
| Cmd+T bar size | Height follows its content | Hard-coded; last row clipped | Fixed |
| Drag between Favorites, pinned tabs, and other tabs | Dropping in a section converts the tab | Not possible | Next |
| Collapsed sidebar | Hovering the window edge slides it out over the page | Disabled under focus mode | Next |
| Tab rows | Hover background fades; close button fades in on hover | Brave defaults | Next |
| Copy URL | Cmd+Shift+C with a short confirmation toast | None | Next |
| Split view | Drag a tab to the page edge; the split preview snaps | Brave split view, no drag gesture | Later |
| Sidebar collapse and expand | Width animates | Brave already animates it | Keep |

Native unit tests cover drag ordering, cancellation, and the click/drag
distinction. Motion itself needs a visual check in the running app.
