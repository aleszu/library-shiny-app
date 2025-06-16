from shiny import App, ui, render, reactive
from shinywidgets import render_plotly, output_widget, render_widget
from datetime import timedelta
import faicons as fa
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Load data
branch_names = pd.read_csv("cplbranches/data/branch_names_crosswalk.csv")
visits_data_all = pd.read_csv("cplbranches/data/visits_data_all.csv")
public_calendar = pd.read_csv("cplbranches/data/public_calendar.csv")
branch_service_census_food_data = pd.read_csv("cplbranches/data/branch_service_census_food_data.csv")
comp_use = pd.read_csv("cplbranches/data/branch_computer_use.csv")
branch_titles_filtered = pd.read_csv("cplbranches/data/branch_titles_filtered.csv")
branch_physical_reading = pd.read_csv("cplbranches/data/branch_physical_reading_fix.csv")

# Ensure medianincome is numeric
branch_service_census_food_data['medianincome'] = pd.to_numeric(branch_service_census_food_data['medianincome'], errors='coerce')

ICONS = {
    "income": fa.icon_svg("money-bill"),
    "user": fa.icon_svg("user"),
    "computer": fa.icon_svg("computer"),
    "clock": fa.icon_svg("clock"),
}

category_map = {
    "physical_item_adult": "Adult",
    "physical_item_ya": "Young Adult",
    "physical_item_juvenile": "Juvenile"
}

# Define UI
app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.output_ui("cpllogo"),

            ui.input_select(
                "branch", "Select branch",
                choices=branch_names["branch_name"].unique().tolist(),
                selected=branch_names["branch_name"].unique()[3]
            ),

            # Map here

            # ui.h4("Demographics"),
            
            ui.a("Median income"),
            ui.output_text("median_income_display"),

            ui.a("Residents without health insurance"),
            ui.output_text("uninsured_display"),

            ui.a("Unemployment rate"),
            ui.output_text("unemployment_display"),

            ui.a("Residents who are food insecure"),
            ui.output_text("food_display"),

            ui.a("Age distribution"),
            output_widget("age_bar_chart"),

            ui.a("Race/ethnicity"),
            output_widget("race_bar_chart"),

        ),  

        ui.navset_tab(  
        
        ui.nav_panel("Circulation", 
                     
                     ui.h4("Top titles, genres, and reading levels"),
                     ui.tags.br(),
                        ui.layout_columns(
                            ui.card(
                                output_widget("readinglevels_plot"),
                                full_screen=True
                            ),
                            ui.card(
                                ui.a("Checkouts by reading level since 2023"),
                                output_widget("reading_level_donut_chart"),
                                ui.output_data_frame("top_reading_level_table"),
                                full_screen=True
                            ),
                            col_widths=[8,4]
                        ),
                        ui.layout_columns(
                            ui.card(
                                ui.a("Top genres checked out since 2023"),
                                ui.output_data_frame("top_genres_table"),
                                full_screen=True
                            ),
                            ui.card(
                                ui.a("Top books checked out since 2023"),
                                ui.output_data_frame("top_books_table"),
                                full_screen=True
                            ),
                            ui.card(
                                ui.a("Top DVDs checked out since 2023"),
                                ui.output_data_frame("top_dvds_table"),
                                full_screen=True
                            ),
                            col_widths=[4,4,4]
                        )
                     
                     ),

        ui.nav_panel("Visits, Programs, and Computers", 
            ui.h4("Visits and programs held"),
            ui.tags.br(),

                    ui.layout_columns(
                        ui.card(
                            output_widget("visits_plot"),
                            full_screen=True
                        ),
                        col_widths=[12]
                        ),
                    
                    ui.layout_columns(
                        ui.card(
                            output_widget("programs_plot"),
                            full_screen=True
                        ),
                        ui.card(
                        output_widget("scatter_plot"),
                        full_screen=True
                        ),
                        col_widths=[6,6]
                        # ui.output_ui("map")
                    ),
                     ui.h4("Computer usage"),
                     ui.layout_columns(
                        ui.value_box(
                           "Total stations",
                           ui.output_ui("stations"),
                           showcase=ICONS["computer"]
                        ),
                        ui.value_box(
                           "Total sessions",
                           ui.output_ui("sessions"),
                           showcase=ICONS["user"] 
                        ),
                        ui.value_box(
                           "Average session length",
                           ui.output_ui("average_session_length"),
                           showcase=ICONS["clock"]
                        ),
                        col_widths=[4,4,4]
                        )

                     ),
        id="tab",  
        ),       
    ),
    title="CPL Branch Report"
)

# Define server
def server(input, output, session):
    @render.image
    def image():
        from pathlib import Path
        dir = Path(__file__).resolve().parent
        img = {"src": str(dir / "cplbranches/cpl-logo.svg"), "height":'70px', "style":"height='10px' !important"}
        return img
    
    @render.image
    def map_image():
        from pathlib import Path
        base_dir = Path(__file__).resolve().parent
        map_dir = base_dir / "cplbranches/maps"

        # Sanitize and format filename (ensure branch input matches file naming)
        branch_name = input.branch().replace(" ", "_")  # adapt if more cleaning is needed
        filename = f"map_{branch_name}.png"
        full_path = map_dir / filename

        if not full_path.exists():
            return {"src": "", "alt": f"Map not found: {filename}"}

        return {
            "src": str(full_path),
            "width": "100%",  # or a fixed width like "800px"
            "style": "border: 1px solid #ccc;"
        }

    @render.ui
    def map():
        return ui.output_image("map_image", height="70px")

    @render.ui
    def cpllogo():
        return ui.output_image("image", height="70px")

    @render.text
    def median_income_display():
        selected_branch = input.branch()
        filtered_data = branch_service_census_food_data[
            branch_service_census_food_data['branch_name'] == selected_branch
        ]
        
        if not filtered_data.empty:
            median_income_value = filtered_data['medianincome'].iloc[0]
            if pd.notna(median_income_value):
                return f"${median_income_value:,.2f}"
            else:
                return "Data not available"
        else:
            return "No data found"
    
    @render.text
    def food_display():
        selected_branch = input.branch()
        filtered_data = branch_service_census_food_data[
            branch_service_census_food_data['branch_name'] == selected_branch
        ]
        
        if not filtered_data.empty:
            food_value = filtered_data['overall_food_insecurity_rate'].iloc[0]
            if pd.notna(food_value):
                return f"{food_value:,.1%}"
            else:
                return "Data not available"
        else:
            return "No data found"

    @render.text
    def unemployment_display():
        selected_branch = input.branch()
        filtered_data = branch_service_census_food_data[
            branch_service_census_food_data['branch_name'] == selected_branch
        ]
        
        if not filtered_data.empty:
            unemployment_value = filtered_data['unemployment'].iloc[0]
            if pd.notna(unemployment_value):
                return f"{unemployment_value:,.1%}"
            else:
                return "Data not available"
        else:
            return "No data found"

    @render.text
    def uninsured_display():
        selected_branch = input.branch()
        filtered_data = branch_service_census_food_data[
            branch_service_census_food_data['branch_name'] == selected_branch
        ]
        
        if not filtered_data.empty:
            uninsured_value = filtered_data['uninsured'].iloc[0]
            if pd.notna(uninsured_value):
                return f"{uninsured_value:,.1%}"
            else:
                return "Data not available"
        else:
            return "No data found"

    @render_plotly
    def age_bar_chart():
        census_data = branch_service_census_food_data[branch_service_census_food_data["branch_name"] == input.branch()]
        age_columns = ['under10', 'age10to20', 'age20to40', 'age40to60', 'age60plus']
        age_labels = ['<10', '10–19', '20–39', '40–59', '60+']
        values = [census_data.iloc[0][col] for col in age_columns]
        
        age_bar_chart = go.Figure(data=[
            go.Bar(x=age_labels, y=values)
        ])
        age_bar_chart.update_layout(
            # title='Age distribution',
            template='plotly_white'
        )
        return age_bar_chart
    
    @render_plotly
    def race_bar_chart():
        census_data = branch_service_census_food_data[branch_service_census_food_data["branch_name"] == input.branch()]
        race_columns = ['black_pop', 'white_pop', 'asian_nhpi_pop', 'latino_pop']
        race_labels = ['Black', 'White', 'Asian', 'Latino']
        values = [census_data.iloc[0][col]*100 for col in race_columns]
        
        race_bar_chart = go.Figure(data=[
            go.Bar(y=values, x=race_labels)
        ])
        race_bar_chart.update_layout(
            template='plotly_white',
            # xaxis_title='Population Proportion',
            yaxis_title='',
            margin=dict(l=0, r=10, t=10, b=10),
            yaxis=dict(ticksuffix='%')
        )
        return race_bar_chart

    @render_plotly
    def visits_plot():
        df_filtered = visits_data_all[visits_data_all["branch_name"] == input.branch()]
        df_filtered = df_filtered.sort_values("month_date")
        
        fig = px.line(df_filtered, x="month_date", y="value", markers=True, title="layout.hovermode='x unified'")
        fig.update_layout(
            title_text='Monthly visits',
            xaxis_title='',
            yaxis_title='',
            template='simple_white',
            font=dict(size=12),
            showlegend=False,
            hovermode="x unified",
            yaxis=dict(tickformat=','),
            modebar=dict(remove=['zoom', 'pan', 'select'])
        )
        fig.update_traces(
            mode="markers+lines",
            hovertemplate=None,
            line=dict(color="#2c3e50", width=1),
            marker=dict(color="#2c3e50", size=6)
        )
        return fig

    @render_plotly
    def programs_plot():
        df_filtered = public_calendar[public_calendar["branch_name"] == input.branch()]
        result = df_filtered.groupby(['audiences']).agg(
            avg_attendance=('actual_attendance', lambda x: x.mean(skipna=True)),
            total_programs=('actual_attendance', 'count')).reset_index() 
        
        audience_order = [
            "Children Ages 0-5",
            "Children Ages 6-11",
            "Teens Ages 12-18",
            "Adults Ages 19+",
            "Seniors",
            "All Ages"
        ]

        result['audiences'] = pd.Categorical(result['audiences'], categories=audience_order, ordered=True)
        result = result.sort_values('audiences')

        fig = px.bar(
                result,
                x='audiences',
                y='avg_attendance',
                title='Average program attendance by age group'
            )
        
        fig.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                template='simple_white',
                yaxis_title='Average attendance',
                xaxis_title='',
                margin=dict(t=60, b=120)
            )
        return fig

    @render_plotly
    def scatter_plot():
        # Filter data
        df_filtered = public_calendar[
            (public_calendar["branch_name"] == input.branch()) &
            (public_calendar["actual_attendance"] < 100)
        ]

        # Create jittered scatterplot
        fig = px.scatter(
            df_filtered,
            x="time_parsed",
            y="actual_attendance",
            hover_data={
            "actual_attendance": True,
            "title": True,
            "time_parsed": False  # hide if already shown as x-axis
        }
        )

        fig.update_traces(marker=dict(size=6, line=dict(width=0)))
        fig.update_layout(
            title="Start time vs. in-person attendance",
            xaxis_title="Start time",
            yaxis_title="Attendance",
            template="simple_white"
        )

        return fig

    @render.ui
    def stations():
        comp_filtered = comp_use[comp_use["branch_name"] == input.branch()]
        if not comp_filtered.empty:
            total_stations = comp_filtered['total_stations'].iloc[0]
            if pd.notna(total_stations):
                return f"{float(total_stations):,.0f}"
            else:
                return "Data not available"
        else:
            return "No data found"

    @render.ui
    def sessions():
        comp_filtered = comp_use[comp_use["branch_name"] == input.branch()]
        if not comp_filtered.empty:
            total_sessions = comp_filtered['total_sessions'].iloc[0]
            if pd.notna(total_sessions):
                return f"{float(total_sessions):,.0f}"
            else:
                return "Data not available"
        else:
            return "No data found"

    @render.ui
    def average_session_length():
        comp_filtered = comp_use[comp_use["branch_name"] == input.branch()]
        if not comp_filtered.empty:
            average_session_length_min = comp_filtered['average_session_length_min'].iloc[0]
            if pd.notna(average_session_length_min):
                return f"{float(average_session_length_min):,.1f} minutes"
            else:
                return "Data not available"
        else:
            return "No data found"

    # Reading levels plot
    @reactive.Calc
    def filtered_branch_physical_reading():
        return branch_physical_reading[branch_physical_reading["branch_name"] == input.branch()]
    
    @reactive.Calc
    def reading_levels_data():
        df = filtered_branch_physical_reading()
        
        long_df = df.melt(
            id_vars=["branch_name", "month"],
            value_vars=[col for col in df.columns if col.startswith("physical_item_")],
            var_name="category",
            value_name="count"
        )

        # Map category codes to labels
        long_df["category"] = long_df["category"].map(category_map)

        return long_df.dropna(subset=["count"])

    @render_plotly
    def readinglevels_plot():
        data = reading_levels_data()
        if data.empty:
            return px.scatter(title="No data available for this branch.")

        fig = px.area(
            data,
            x="month",
            y="count",
            color="category",
            title="Physical item checkouts over time",
            labels={"count": "Checkouts", "month": "Month", "category": "Category"}
        )
        fig.update_layout(
            yaxis=dict(tickformat=","),
            template='simple_white',
            legend_title="Category"
        )
        return fig
    
    #####
    # Top genres table 
    #####
    @reactive.Calc
    def filtered_branch_titles():
        return branch_titles_filtered[branch_titles_filtered["branch_name"] == input.branch()]

    @reactive.Calc
    def genre_tbl():
        df = filtered_branch_titles()
        grouped = (
            df.groupby(["genre"], as_index=False)
              .agg(checkouts=('x_of_checkouts', 'sum'))
        )
        # Sort and get top 20 
        top_genres = (
            grouped.sort_values("checkouts", ascending=False)
                   .head(20)
        )
        top_genres['rank'] = top_genres['checkouts'].rank(method='dense', ascending=False)
        top_genres = top_genres.rename(columns={'rank':'Rank', 'genre':'Genre', 'checkouts':'Checkouts'})
        new_order = ['Rank', 'Genre', 'Checkouts']
        top_genres = top_genres[new_order]
        return top_genres

    @render.data_frame
    def top_genres_table():
        return render.DataTable(genre_tbl(), height="600px")

    #####
    # top_reading_level_table
    #####

    @reactive.Calc
    def summarized_readinglevel_data():
        df = filtered_branch_titles()
        grouped = (
            df
            .groupby(["branch_name", "reading_level_item_cat2"], as_index=False)
            .agg(checkouts=('x_of_checkouts', 'sum'))
        )
        return grouped

    @reactive.Calc
    def reading_levels_tbl():
        df = summarized_readinglevel_data()
        df = df[df["branch_name"] == input.branch()]
        
        # Get top 50 per branch
        top_titles = df.sort_values("checkouts", ascending=False).head(50)
        top_titles = top_titles.drop(columns=['branch_name'], axis=1)
        top_titles = top_titles.rename(columns={'reading_level_item_cat2':'Reading level', 'title':'Title', 'checkouts':'Checkouts'})
        return top_titles

    @render.data_frame
    def top_reading_level_table():
        return render.DataTable(reading_levels_tbl(), height="200px")

    @render_widget
    def reading_level_donut_chart():
        df = reading_levels_tbl()
        if df.empty:
            return px.scatter(title="No data available for selected branch.")
        
        fig = px.pie(
            df,
            names="Reading level",
            values="Checkouts",
            hole=0.4,
            title=""
        )
        fig.update_traces(textinfo="percent+label", pull=[0.03]*len(df))
        fig.update_layout(showlegend=True)

        return fig

    ####################
    # Top books table
    ####################
    @reactive.Calc
    def summarized_data():
        df = filtered_branch_titles()
        grouped = (
            df
            .groupby(["branch_name", "material_type_item_cat1", "title"], as_index=False)
            .agg(checkouts=('x_of_checkouts', 'sum'))
        )
        return grouped

    @reactive.Calc
    def books_tbl():
        df = summarized_data()
        df = df[
            (df["material_type_item_cat1"].isin(["BOOKS"])) &
            (df["branch_name"] == input.branch())
        ]
        # Get top 50 per branch
        top_titles = df.sort_values("checkouts", ascending=False).head(50)
        top_titles = top_titles.drop(columns=['branch_name'], axis=1)
        top_titles['rank'] = top_titles['checkouts'].rank(method='dense', ascending=False)
        top_titles = top_titles.rename(columns={'rank':'Rank', 'material_type_item_cat1':'Category', 'title':'Title', 'checkouts':'Checkouts'})
        new_order = ['Rank', 'Title', 'Category', 'Checkouts']
        top_titles = top_titles[new_order]
        return top_titles
    
    @render.data_frame
    def top_books_table():
        return render.DataTable(books_tbl(), height="600px")

    ####################
    # Top DVDs table 
    ####################
    @reactive.Calc
    def dvds_tbl():
        df = summarized_data()
        df = df[
            (df["material_type_item_cat1"].isin(["DVDS", "DVD-BLURAY"])) &
            (df["branch_name"] == input.branch())
        ]
        # Get top 50 per branch
        top_titles = df.sort_values("checkouts", ascending=False).head(50)
        top_titles = top_titles.drop(columns=['branch_name'], axis=1)
        top_titles['rank'] = top_titles['checkouts'].rank(method='dense', ascending=False)
        top_titles = top_titles.rename(columns={'rank':'Rank', 'material_type_item_cat1':'Category', 'title':'Title', 'checkouts':'Checkouts'})
        new_order = ['Rank', 'Title', 'Category', 'Checkouts']
        top_titles = top_titles[new_order]
        return top_titles

    @render.data_frame
    def top_dvds_table():
        return render.DataTable(dvds_tbl(), height="600px")

# Create the app
app = App(app_ui, server)
