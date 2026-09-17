//
// ============================================================================
// DOESBOT CNC CONTROLLER ENCLOSURE -- CLEAN NO-PORT VERSION
// ============================================================================
//
// Parametric two-piece enclosure for:
//
//      PCB: 5.000" x 3.375"
//           127.000 x 85.725 mm
//
// This version intentionally contains NO connector/port cutouts.
//
// Design:
//   - Bottom tray containing the controller PCB
//   - Removable top lid
//   - Four PCB mounting risers
//   - Prototype-adjustable PCB mounting slots
//   - Four enclosure screw bosses
//   - Internal perimeter locating lip
//   - Top exhaust ventilation
//   - Bottom intake ventilation
//   - Simplified PCB/component reference model
//
// PORT STRATEGY:
//   Connector openings are intentionally omitted.
//   Add them later against the actual PCB/assembly geometry.
//
// OpenSCAD units are millimeters.
//
// ============================================================================


// ============================================================================
// 0. RENDER MODE
// ============================================================================
//
// Valid:
//
//      "assembly"
//      "exploded"
//      "bottom"
//      "top"
//      "reference"
//      "mounts"
//      "vents"
//
PART = "assembly";


// ============================================================================
// 1. QUALITY
// ============================================================================

$fn = 48;


// ============================================================================
// 2. PCB DIMENSIONS
// ============================================================================

// Actual board dimensions supplied.
//
// 5.000"
PCB_X = 127.000;

// 3.375"
PCB_Y = 85.725;

// Approximate bare PCB thickness.
PCB_Z = 1.60;


// ============================================================================
// 3. PCB CLEARANCE
// ============================================================================
//
// Horizontal breathing room between PCB edge and enclosure wall.
//

PCB_CLEARANCE_X = 6.0;
PCB_CLEARANCE_Y = 6.0;


// ============================================================================
// 4. PCB VERTICAL STACK
// ============================================================================
//
// PCB is elevated above enclosure floor.
//
// Vertical stack:
//
//      enclosure floor
//          |
//          +-- 7 mm riser
//          |
//          +-- PCB
//          |
//          +-- electronics/components
//          |
//          +-- additional lower-case clearance
//          |
//          +-- enclosure seam
//          |
//          +-- upper wiring volume
//          |
//          +-- roof
//

PCB_STANDOFF_HEIGHT = 7.0;

// Estimated maximum component height above PCB.
PCB_COMPONENT_HEIGHT = 18.0;

// Additional clearance above PCB components before seam.
LOWER_COMPONENT_CLEARANCE = 6.0;

// Wiring / cable bend / service volume inside lid.
TOP_WIRE_CLEARANCE = 24.0;


// ============================================================================
// 5. ENCLOSURE CONSTRUCTION
// ============================================================================

WALL = 2.50;

BOTTOM_FLOOR = 2.50;

TOP_ROOF = 2.50;

CORNER_RADIUS = 5.0;


// ============================================================================
// 6. ENCLOSURE HEIGHTS
// ============================================================================
//
// Bottom wall extends from top surface of floor to enclosure seam.
//

BOTTOM_WALL_HEIGHT =
    PCB_STANDOFF_HEIGHT
    + PCB_Z
    + PCB_COMPONENT_HEIGHT
    + LOWER_COMPONENT_CLEARANCE;


// Total lower enclosure height.
BOTTOM_HEIGHT =
    BOTTOM_FLOOR
    + BOTTOM_WALL_HEIGHT;


// Lid wall provides upper wiring/service volume.
TOP_WALL_HEIGHT =
    TOP_WIRE_CLEARANCE;


// Complete lid height.
TOP_HEIGHT =
    TOP_WALL_HEIGHT
    + TOP_ROOF;


// Complete assembled height.
ASSEMBLED_HEIGHT =
    BOTTOM_HEIGHT
    + TOP_HEIGHT;


// ============================================================================
// 7. ENCLOSURE FOOTPRINT
// ============================================================================

// Internal dimensions.
INNER_X =
    PCB_X
    + PCB_CLEARANCE_X * 2;

INNER_Y =
    PCB_Y
    + PCB_CLEARANCE_Y * 2;


// External dimensions.
OUTER_X =
    INNER_X
    + WALL * 2;

OUTER_Y =
    INNER_Y
    + WALL * 2;


// ============================================================================
// 8. PCB POSITION
// ============================================================================
//
// PCB coordinate convention:
//
//      PCB_ORIGIN_X/Y = lower-left PCB corner
//      PCB_ORIGIN_Z   = bottom surface of PCB
//
// Board is centered inside enclosure.
//

PCB_ORIGIN_X =
    WALL
    + PCB_CLEARANCE_X;

PCB_ORIGIN_Y =
    WALL
    + PCB_CLEARANCE_Y;

PCB_ORIGIN_Z =
    BOTTOM_FLOOR
    + PCB_STANDOFF_HEIGHT;


// ============================================================================
// 9. PCB MOUNTING HOLE LOCATIONS
// ============================================================================
//
// IMPORTANT:
//
// These remain PLACEHOLDER positions.
//
// They currently assume mounting-hole centers approximately 4 mm
// inward from each PCB edge.
//
// Unlike the old version, the individual coordinates are explicitly
// represented here. That makes it easy to replace them with actual
// measured locations later.
//
// Coordinates are PCB-relative.
//
// Example:
//
//      PCB_HOLE_X1 = measured distance from left PCB edge
//      PCB_HOLE_X2 = measured distance from left PCB edge
//
//      PCB_HOLE_Y1 = measured distance from front PCB edge
//      PCB_HOLE_Y2 = measured distance from front PCB edge
//

PCB_HOLE_X1 = 4.0;
PCB_HOLE_X2 = PCB_X - 4.0;

PCB_HOLE_Y1 = 4.0;
PCB_HOLE_Y2 = PCB_Y - 4.0;


// ============================================================================
// 10. PCB RISER GEOMETRY
// ============================================================================

// Outside diameter of PCB riser.
PCB_BOSS_OD = 8.0;

// Screw/clearance-hole diameter.
PCB_BOSS_HOLE = 3.2;


// --------------------------------------------------------------------------
// Prototype adjustment slots
// --------------------------------------------------------------------------
//
// true:
//
//      elongated holes provide tolerance during first fit.
//
// false:
//
//      ordinary circular mounting holes.
//
PCB_USE_ADJUSTMENT_SLOTS = true;


// Total center-to-center slot travel.
//
// Increased from the original 4 mm to 8 mm for the prototype.
//
// This does NOT make the actual mounting-hole coordinates optional.
// Once the real board dimensions are confirmed, replace the placeholder
// coordinates above and reduce/disable the slots.
//
PCB_SLOT_TRAVEL = 8.0;


// Slot orientation.
//
// "x" = slot extends along enclosure X
// "y" = slot extends along enclosure Y
//
PCB_SLOT_AXIS = "x";


// ============================================================================
// 11. ENCLOSURE SCREW BOSSES
// ============================================================================
//
// Four structural bosses join bottom enclosure to lid.
//

CASE_SCREW_DIAMETER = 3.2;

CASE_BOSS_OD = 9.0;


// Boss center distance from INNER enclosure corner.
CASE_BOSS_INSET = 7.0;


// Boss locations.
CASE_BOSS_X1 =
    WALL
    + CASE_BOSS_INSET;

CASE_BOSS_X2 =
    OUTER_X
    - WALL
    - CASE_BOSS_INSET;

CASE_BOSS_Y1 =
    WALL
    + CASE_BOSS_INSET;

CASE_BOSS_Y2 =
    OUTER_Y
    - WALL
    - CASE_BOSS_INSET;


// ============================================================================
// 12. LID LOCATING LIP
// ============================================================================
//
// Bottom enclosure gets a raised internal perimeter tongue.
//
// Lid receives a slightly enlarged mating cavity.
//
// For an initial PLA print:
//
//      0.30 mm clearance per side
//
// is intentionally conservative.
//

LIP_HEIGHT = 3.0;

LIP_THICKNESS = 1.5;

LIP_CLEARANCE = 0.30;


// ============================================================================
// 13. TOP VENTILATION
// ============================================================================

TOP_VENT_COUNT = 9;

TOP_VENT_LENGTH = 52;

TOP_VENT_WIDTH = 2.4;

TOP_VENT_SPACING = 5.0;


// Position of top exhaust bank.
TOP_VENT_CENTER_X =
    OUTER_X * 0.35;

TOP_VENT_CENTER_Y =
    OUTER_Y * 0.50;


// ============================================================================
// 14. BOTTOM VENTILATION
// ============================================================================

BOTTOM_VENT_COUNT = 7;

BOTTOM_VENT_LENGTH = 42;

BOTTOM_VENT_WIDTH = 2.0;

BOTTOM_VENT_SPACING = 5.0;


// Position of bottom intake bank.
BOTTOM_VENT_CENTER_X =
    OUTER_X * 0.68;

BOTTOM_VENT_CENTER_Y =
    OUTER_Y * 0.50;


// ============================================================================
// 15. DEBUG / REFERENCE COLORS
// ============================================================================

COLOR_BOTTOM =
    [0.22, 0.25, 0.28];

COLOR_TOP =
    [0.32, 0.35, 0.38];

COLOR_PCB =
    [0.08, 0.25, 0.10];

COLOR_COMPONENT =
    [0.15, 0.15, 0.15];

COLOR_MOUNT =
    [0.75, 0.45, 0.10];

COLOR_VENT =
    [0.15, 0.45, 0.85, 0.60];


// ============================================================================
// 16. HELPER -- ROUNDED RECTANGULAR PRISM
// ============================================================================

module rounded_box(
    size = [10, 10, 10],
    radius = 2
)
{
    x = size[0];
    y = size[1];
    z = size[2];

    hull()
    {
        translate([
            radius,
            radius,
            0
        ])
        cylinder(
            r = radius,
            h = z
        );

        translate([
            x - radius,
            radius,
            0
        ])
        cylinder(
            r = radius,
            h = z
        );

        translate([
            radius,
            y - radius,
            0
        ])
        cylinder(
            r = radius,
            h = z
        );

        translate([
            x - radius,
            y - radius,
            0
        ])
        cylinder(
            r = radius,
            h = z
        );
    }
}


// ============================================================================
// 17. HELPER -- 2D ROUNDED PROFILE
// ============================================================================

module rounded_profile_2d(
    x,
    y,
    radius
)
{
    hull()
    {
        translate([
            radius,
            radius
        ])
        circle(
            r = radius
        );

        translate([
            x - radius,
            radius
        ])
        circle(
            r = radius
        );

        translate([
            radius,
            y - radius
        ])
        circle(
            r = radius
        );

        translate([
            x - radius,
            y - radius
        ])
        circle(
            r = radius
        );
    }
}


// ============================================================================
// 18. HELPER -- VENT SLOT
// ============================================================================
//
// Creates a capsule-shaped ventilation slot.
//

module vent_slot(
    length,
    width,
    height
)
{
    hull()
    {
        translate([
            -length / 2 + width / 2,
            0,
            0
        ])
        cylinder(
            d = width,
            h = height
        );

        translate([
            length / 2 - width / 2,
            0,
            0
        ])
        cylinder(
            d = width,
            h = height
        );
    }
}


// ============================================================================
// 19. PCB REFERENCE MODEL
// ============================================================================
//
// Simplified model used ONLY for fit visualization.
//
// It is not part of printable bottom/top exports.
//

module pcb_reference()
{
    // ----------------------------------------------------------------------
    // PCB substrate
    // ----------------------------------------------------------------------

    color(COLOR_PCB)
    translate([
        PCB_ORIGIN_X,
        PCB_ORIGIN_Y,
        PCB_ORIGIN_Z
    ])
    cube([
        PCB_X,
        PCB_Y,
        PCB_Z
    ]);


    // ----------------------------------------------------------------------
    // Approximate component envelope
    // ----------------------------------------------------------------------

    color(COLOR_COMPONENT)
    translate([
        PCB_ORIGIN_X + 5,
        PCB_ORIGIN_Y + 5,
        PCB_ORIGIN_Z + PCB_Z
    ])
    cube([
        PCB_X - 10,
        PCB_Y - 10,
        PCB_COMPONENT_HEIGHT
    ]);


    // ----------------------------------------------------------------------
    // Mounting-hole references
    // ----------------------------------------------------------------------

    for (x = [
        PCB_HOLE_X1,
        PCB_HOLE_X2
    ])
    for (y = [
        PCB_HOLE_Y1,
        PCB_HOLE_Y2
    ])
    {
        color("silver")

        translate([
            PCB_ORIGIN_X + x,
            PCB_ORIGIN_Y + y,
            PCB_ORIGIN_Z - 0.5
        ])

        cylinder(
            d = PCB_BOSS_HOLE,
            h = PCB_Z + 1
        );
    }
}


// ============================================================================
// 20. PCB MOUNTING RISER
// ============================================================================
//
// Structural riser supporting PCB.
//
// Height:
//
//      floor surface
//          |
//          +---- PCB_STANDOFF_HEIGHT
//          |
//      PCB bottom
//

module pcb_mount_boss()
{
    difference()
    {
        // Main riser.
        cylinder(
            d = PCB_BOSS_OD,
            h = PCB_STANDOFF_HEIGHT
        );


        // ------------------------------------------------------------------
        // Adjustable prototype slot
        // ------------------------------------------------------------------

        if (PCB_USE_ADJUSTMENT_SLOTS)
        {
            if (PCB_SLOT_AXIS == "x")
            {
                hull()
                {
                    translate([
                        -PCB_SLOT_TRAVEL / 2,
                        0,
                        -1
                    ])
                    cylinder(
                        d = PCB_BOSS_HOLE,
                        h = PCB_STANDOFF_HEIGHT + 2
                    );

                    translate([
                        PCB_SLOT_TRAVEL / 2,
                        0,
                        -1
                    ])
                    cylinder(
                        d = PCB_BOSS_HOLE,
                        h = PCB_STANDOFF_HEIGHT + 2
                    );
                }
            }

            else
            {
                hull()
                {
                    translate([
                        0,
                        -PCB_SLOT_TRAVEL / 2,
                        -1
                    ])
                    cylinder(
                        d = PCB_BOSS_HOLE,
                        h = PCB_STANDOFF_HEIGHT + 2
                    );

                    translate([
                        0,
                        PCB_SLOT_TRAVEL / 2,
                        -1
                    ])
                    cylinder(
                        d = PCB_BOSS_H