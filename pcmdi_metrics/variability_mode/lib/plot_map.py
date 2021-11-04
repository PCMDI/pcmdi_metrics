import vcs


def plot_map(mode, model, syear, eyear, season, eof_Nth, frac_Nth, output_file_name):
    # Create a VCS canvas
    canvas = vcs.init(geometry=(900, 800), bg=1)  # Plotting in background mode

    # Turn off unnecessary information, avoiding text overlapping
    canvas.drawlogooff()
    tmpl = vcs.createtemplate()
    tmpl.blank(
        [
            "title",
            "mean",
            "min",
            "max",
            "dataname",
            "crdate",
            "crtime",
            "units",
            "zvalue",
            "tvalue",
            "xunits",
            "yunits",
            "xname",
            "yname",
        ]
    )

    # Color scheme and levels
    canvas.setcolormap("bl_to_darkred")
    gm = canvas.createisofill()  # Graphic method
    if mode.split("_")[0] in ["PDO", "NPGO"]:
        gm.levels = [-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5]
    else:
        gm.levels = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
    gm.ext_1 = "y"  # Extend left side colorbar edge
    gm.ext_2 = "y"  # Extend right side colorbar edge
    cols = vcs.getcolors(gm.levels, list(range(16, 240)), split=0)
    gm.fillareacolors = cols
    gm.missing = 0

    # Map Projection
    if mode in ["NAO", "PNA", "NPO", "PDO", "AMO", "NPGO"]:
        gm.projection = "lambert"
    elif mode in ["PDO_teleconnection", "NPGO_teleconnection"]:
        gm.projection = "robinson"
    else:
        gm.projection = "polar"
        tmpl.ytic1.priority = 0
        tmpl.ytic2.priority = 0

    # Remove white gap along longitude 0 when plot on polar projection
    if mode.split("_")[0] in ["SAM", "NAM"]:
        eof_Nth = eof_Nth(longitude=(-180, 185))

    # Plotting domain
    xtra = {}
    if mode.split("_")[0] in ["PDO", "NPGO"]:  # Global
        pass
    elif mode.split("_")[0] == "SAM":  # Southern Hemisphere
        xtra["latitude"] = (-90.0, 0.0)
    else:  # Northern Hemisphere
        xtra["latitude"] = (90.0, 0.0)
    eof_Nth = eof_Nth(**xtra)

    # Plot
    canvas.plot(eof_Nth, gm, tmpl)

    # Title
    plot_title = vcs.createtext()
    plot_title.x = 0.5
    plot_title.y = 0.97
    plot_title.height = 30
    plot_title.halign = "center"
    plot_title.valign = "top"
    plot_title.color = "black"
    if frac_Nth != -999:
        percentage = (
            str(round(float(frac_Nth * 100.0), 1)) + "%"
        )  # % with one floating number
    else:
        percentage = ""
    plot_title.string = (
        mode
        + ": "
        + model
        + "\n"
        + str(syear)
        + "-"
        + str(eyear)
        + " "
        + season
        + " "
        + percentage
    )
    canvas.plot(plot_title)

    # Save image file
    canvas.png(output_file_name + ".png")
    # Close canvas
    canvas.clear()
    canvas.close()
