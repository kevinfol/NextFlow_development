def initOptions():
    with open("resources/temp/user_set_options.txt", 'w') as writefile:
        writefile.write("""
[DATASETS TAB]
current_map_location=
current_map_layers=

[DATA TAB]
por_start=
current_plotted_columns=
current_plot_bounds=""")