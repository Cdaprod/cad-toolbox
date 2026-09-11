# Common workflows

## Inspect a downloaded STL

```bash
cad inspect downloaded.stl
```

## Repair and normalize a mesh

```bash
cad repair downloaded.stl repaired.stl
cad align repaired.stl normalized.stl --center-xy --bottom-z
```

## Convert inches to millimeters

```bash
cad scale source.stl source-mm.stl --factor 25.4
```

## Make a STEP cutter

```bash
cad make port-cutter usb-c.step \
  --width 9.2 --height 3.6 --depth 12 --clearance 0.35
```

## Cut a STEP enclosure

```bash
cad boolean cut enclosure.step usb-c.step enclosure-cut.step
```

## Work from iPhone

SSH into the MacBook, run the CLI there, and write outputs into a folder exposed
through the iOS Files app or Working Copy checkout.
