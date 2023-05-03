from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.image('./images/background.png', x = 0, y = 0, w = 210)

def generate_pdf_report(g):
    now = datetime.now()
    time_pdf_name = now.strftime("%b-%d-%Y at %Hh%Mm%Ss")
    # time_title = now.strftime("%b-%d-%Y, Time: %H:%M:%S")
    # Recopilation of executed tasks
    executed_task = [[g.player_one.individual_score.take_flashlight,   g.player_two.individual_score.take_flashlight],
                    [g.player_one.individual_score.use_flashlight,     g.player_two.individual_score.use_flashlight],
                    [g.player_one.individual_score.take_right_suit,    g.player_two.individual_score.take_right_suit],
                    [g.player_one.individual_score.take_right_filter,  g.player_two.individual_score.take_right_filter],
                    [g.player_one.individual_score.take_camera,        g.player_two.individual_score.take_camera],
                    [g.player_one.individual_score.take_sampling_kit,  g.player_two.individual_score.take_sampling_kit],
                    [g.player_one.individual_score.take_chem_detector, g.player_two.individual_score.take_chem_detector],
                    [g.player_one.individual_score.take_decon_kit,     g.player_two.individual_score.take_decon_kit],                        
                    [g.player_one.individual_score.take_gun,           g.player_two.individual_score.take_gun],
                    [g.player_one.individual_score.irradiation,        g.player_two.individual_score.irradiation]]
    print("Individual Tasks: ", executed_task)
    team_executed_task = [sum(g.team_score.take_samples.values()),sum(g.team_score.take_pictures.values()),g.team_score.use_lift] #,g.team_score.inspect_body]
    print("Team Tasks: ", team_executed_task)
    # Instantiation of inherited class
    pdf = PDF(orientation = 'P', unit = 'mm', format = 'A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    # DATE
    pdf.set_font('Helvetica', 'IB', 10)
    pdf.set_text_color(114, 148, 182)
    pdf.cell(2, 0, 'Date: {}'.format(now.strftime("%b-%d-%Y, Time: %H:%M:%S")), 0, 0)

    # SETTINGS TAB
    pdf.set_text_color(182, 223, 244)
    current_y = 50
    pdf.set_xy(38,current_y)
    pdf.cell(10, 10, '     Permissive           Non-Permissive', 0, 0, "C")
    if g.permissiveness: pdf.image('./images/Selection.png', x = 12, y = current_y, w = 30)
    else: pdf.image('./images/Selection.png', x = 45, y = current_y, w = 30)
    pdf.set_xy(39,current_y+15)
    pdf.cell(10, 10, '  Tracking              Non-Tracking', 0, 0, "C")
    if g.tracking: pdf.image('./images/Selection.png', x = 12, y = current_y+15, w = 30)
    else: pdf.image('./images/Selection.png', x = 45, y = current_y+15, w = 30)
    pdf.set_xy(38,current_y+30)
    pdf.cell(10, 10, ' Multiplayer             Singleplayer', 0, 0, "C")
    if g.is_multiplayer: pdf.image('./images/Selection.png', x = 12, y = current_y+30, w = 30)
    else: pdf.image('./images/Selection.png', x = 45, y = current_y+30, w = 30)
    # Line break
    pdf.ln(20)

    # PLAYERS TAB
    current_x = 100
    current_y = 53
    pdf.set_text_color(182, 223, 244)
    pdf.set_font('Helvetica', 'I', 12)
    pdf.set_xy(current_x, current_y)
    pdf.cell(30, 10, 'Player One: {}'.format(g.player_one.name), 0, 0)
    pdf.image('./images/Profile.png', x = current_x-10, y = current_y, w = 8)
    if g.is_multiplayer:
        pdf.set_xy(current_x,current_y+12)
        pdf.cell(30, 10, 'Player Two: {}'.format(g.player_two.name), 0, 0)
        pdf.image('./images/Profile.png', x = current_x-10, y = current_y+12, w = 8)

    # INDIVIDUAL TASKS TAB
    current_x = 5
    current_y = 95
    pdf.set_text_color(182, 223, 244)
    pdf.set_font('Helvetica', '', 12)
    pdf.set_xy(current_x,current_y+2)
    current_y = current_y + 10
    start_checks = current_x + 54
    start_checks_player2_offset = 17
    pdf.set_xy(start_checks+32,current_y)
    pdf.set_text_color(110, 149, 183)
    pdf.cell(25, 5, "P1", 0, 0,'C')

    if g.is_multiplayer:
        pdf.set_xy(start_checks+67,current_y)
        pdf.cell(25, 5, "P2", 0, 0,'C')

    for i in range(len(g.task_individual)):
        if (g.task_individual[i] == "Take the gun" and g.permissiveness): 
            continue
        pdf.set_text_color(182, 223, 244)
        formula_y = 50*(i+1)*0.19 + current_y-2
        pdf.set_xy(current_x+5,formula_y)
        pdf.cell(0, 10, g.task_individual[i], 0, 1)
        pdf.image('./images/task{}.png'.format(i+1), x = current_x+58, y = formula_y, w = 9)
        
        if g.task_individual[i] != "Irradiation":
            # Player One
            if executed_task[i][0]: pdf.image('./images/yes.png', x = start_checks+40, y = formula_y, w = 9)
            else: pdf.image('./images/no.png', x = start_checks+40, y = formula_y, w = 9)
            # Player Two
            if g.is_multiplayer:
                if executed_task[i][1]: pdf.image('./images/yes.png', x = start_checks + start_checks_player2_offset + 58, y = formula_y, w = 9)
                else: pdf.image('./images/no.png', x = start_checks + start_checks_player2_offset + 58, y = formula_y, w = 9)
        else:
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(110, 149, 183)
            pdf.set_xy(start_checks+32,formula_y+2)
            pdf.cell(25, 5, f"{executed_task[i][0]} microSv", 0, 0,'C')
            if g.is_multiplayer:
                pdf.set_xy(start_checks + start_checks_player2_offset + 50,formula_y+2)
                pdf.cell(25, 5, f"{executed_task[i][1]} microSv", 0, 0,'C')
            
        if g.task_individual[i] == "Take right suit":
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(110, 149, 183)
            pdf.set_xy(start_checks + 92,formula_y+2)
            pdf.cell(25, 5, f"Correct suit: Chem. Proof Gear", 0, 0) #TODO: add condition that triggers the comment

        if g.task_individual[i] == "Take right filter":
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(110, 149, 183)
            pdf.set_xy(start_checks + 92,formula_y+2)
            pdf.cell(25, 5, f"Correct filter: Multipurpose Filter", 0, 0) #TODO: add condition that triggers the comment
        
        if g.task_individual[i] == "Irradiation":
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(110, 149, 183)
            pdf.set_xy(start_checks + 92,formula_y+2)
            if g.is_multiplayer: pdf.cell(25, 5, f"P1:{g.player_one.individual_score.irradiation_message} | P2:{g.player_two.individual_score.irradiation_message} (radiation dose)", 0, 0)
            else: pdf.cell(25, 5, f"{g.player_one.individual_score.irradiation_message} radiation dose", 0, 0)

        pdf.set_font('Helvetica', '', 12)
        if i == len(g.task_individual)-1:
            pdf.set_xy(start_checks + 17, formula_y + 12)
            pdf.cell(25, 5, "Score:", 0, 0,'C')
            if g.is_multiplayer:
                pdf.set_xy(start_checks + 32, formula_y + 12)
                pdf.cell(25, 5, str(g.player_one.individual_score.score), 0, 0,'C')
                pdf.set_xy(start_checks + start_checks_player2_offset + 50, formula_y + 12)
                pdf.cell(25, 5, str(g.player_two.individual_score.score), 0, 0,'C')
            else:
                pdf.set_xy(start_checks + 32, formula_y + 12)
                pdf.cell(25, 5, str(g.player_one.individual_score.score), 0, 0,'C')
    
    # TEAM TASKS TAB
    current_x = 5
    current_y = 219
    pdf.set_xy(current_x,current_y+2)
    current_y = current_y + 10
    start_checks = current_x + 64
    pdf.set_xy(start_checks-9,current_y)

    for i in range(len(g.task_team)):
        formula_y = 50*(i+1)*0.19 + current_y-2
        pdf.set_xy(current_x+5,formula_y)
        pdf.set_text_color(182, 223, 244)
        pdf.cell(0, 10, g.task_team[i], 0, 1)
        pdf.image('./images/team_task{}.png'.format(i+1), x = current_x+58, y = formula_y, w = 9)
        if g.task_team[i] == "Use lift": #or g.task_team[i] == "Inspect body":
            if team_executed_task[i]: pdf.image('./images/yes.png', x = start_checks+30, y = formula_y, w = 9)
            else: pdf.image('./images/no.png', x = start_checks+30, y = formula_y, w = 9)
        else:
            pdf.set_font('Helvetica', '', 12)
            pdf.set_xy(start_checks+22,formula_y+2)
            pdf.set_text_color(110, 149, 183)
            if g.task_team[i] == "Samples taken" : pdf.cell(25, 5, f"{team_executed_task[i]}/{g.team_score.total_samples}", 0, 0,'C')
            elif g.task_team[i] == "Pictures taken" : pdf.cell(25, 5, f"{team_executed_task[i]}/{g.team_score.total_pictures}", 0, 0,'C')
            
    current_x = 144
    current_y = 250
    pdf.set_xy(current_x,current_y)
    pdf.set_text_color(182, 223, 244)
    pdf.set_font('Helvetica', '', 60)
    pdf.cell(50, 20, str(g.total_score), 0, 1,"C")

    print("Today's date:", now)
    pdf.output(f'/home/calvarina/Desktop/Reports/Calvarina Report {time_pdf_name}.pdf', 'F')