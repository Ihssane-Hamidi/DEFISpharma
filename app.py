"""
app.py — Point d'entrée principal
TPI · Analyse Financière (Dash + flask-login)
"""

import dash
from dash import Dash, dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from flask import Flask, redirect, request
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    current_user,
)

from data import (
    load_mq, load_mq_prix, load_act, load_act_prix, load_brent,
    prepare_valid_mq, prepare_valid_act,
    PERIODS_LABELS,
)
from utils import detect_oil_rallies

from pages.accueil     import layout as layout_accueil
from pages.societe     import layout as layout_societe,     register_callbacks as cb_societe
from pages.panel       import layout as layout_panel
from pages.brent       import layout as layout_brent,       register_callbacks as cb_brent
from pages.ols         import layout as layout_ols,         register_callbacks as cb_ols
from pages.strategique import layout as layout_strategique, register_callbacks as cb_strategique
from pages.composite   import layout as layout_composite,   register_callbacks as cb_composite


# ══════════════════════════════════════════════════════════════════════════════
# FLASK + LOGIN CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
server = Flask(__name__)
server.config.update(SECRET_KEY='ma-clé-DEFIS')

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'


class User(UserMixin):
    def __init__(self, id):
        self.id = id


USER_DB = {"analyst": "tpi2025"}


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@server.before_request
def require_login():
    allowed = ['/login', '/logout', '/_dash-', '/assets']
    if any(request.path.startswith(p) for p in allowed):
        return
    if not current_user.is_authenticated:
        return redirect('/login')


# ── ROUTES FLASK (LOGIN/LOGOUT) ───────────────────────────────────────────────
@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USER_DB and USER_DB[username] == password:
            login_user(User(username))
            return redirect('/')
        return _login_page(error="Identifiants incorrects")
    return _login_page()


@server.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


def _login_page(error=None):
    error_html = (
        f'<div style="color: #f85149; text-align: center; margin-bottom: 15px;">{error}</div>'
        if error else ''
    )
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>TPI · Connexion</title>
        <style>
            body {{ background: #0d1117; color: #e6edf3; font-family: -apple-system, sans-serif;
                    display: flex; justify-content: center; align-items: center;
                    height: 100vh; margin: 0; }}
            .login-card {{ background: #161b22; padding: 30px; border-radius: 8px;
                           border: 1px solid #30363d; width: 320px;
                           box-shadow: 0 8px 24px rgba(0,0,0,0.5); }}
            .login-title {{ font-size: 1.2rem; font-weight: 600; margin-bottom: 20px;
                            text-align: center; color: #58a6ff; }}
            .login-input {{ width: 100%; padding: 12px; margin: 8px 0;
                            background: #0d1117; border: 1px solid #30363d;
                            color: white; border-radius: 6px; box-sizing: border-box; }}
            .login-btn {{ width: 100%; padding: 12px; background: #238636; border: none;
                          color: white; border-radius: 6px; cursor: pointer;
                          font-weight: 600; margin-top: 15px; }}
            .login-btn:hover {{ background: #2ea043; }}
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="login-title">TPI · Analyse Financière</div>
            {error_html}
            <form method="POST">
                <input class="login-input" type="text" name="username"
                       placeholder="Identifiant" autofocus required>
                <input class="login-input" type="password" name="password"
                       placeholder="Mot de passe" required>
                <button class="login-btn" type="submit">Se connecter</button>
            </form>
        </div>
    </body>
    </html>
    """


# ══════════════════════════════════════════════════════════════════════════════
# DASH APP INITIALIZATION
# ══════════════════════════════════════════════════════════════════════════════
app = Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title='TPI Analyse Financière'
)

# ── CHARGEMENT GLOBAL DES DONNÉES ─────────────────────────────────────────────
try:
    prices_mq  = load_mq_prix()
    df_mq      = load_mq()
    valid_mq   = prepare_valid_mq(df_mq)

    prices_act = load_act_prix()
    df_act     = load_act()
    valid_act  = prepare_valid_act(df_act)

    brent      = load_brent()
    rallies    = detect_oil_rallies(brent)

    APP_DATA = {
        'mq':      {'valid': valid_mq,  'prices': prices_mq},
        'act':     {'valid': valid_act, 'prices': prices_act},
        'brent':   brent,
        'rallies': rallies,
    }

except Exception as e:
    import traceback
    traceback.print_exc()
    APP_DATA = {}


# ── LAYOUT DYNAMIQUE (SÉCURISÉ) ───────────────────────────────────────────────
def serve_layout():
    if not current_user.is_authenticated:
        return html.Div([
            dcc.Location(id='url-login', pathname='/login', refresh=True)
        ])

    return html.Div([
        dcc.Location(id='url', refresh=False),

        # Sidebar
        html.Div(className='sidebar', children=[
            html.Div(className='sidebar-header', children=[
                html.Div("TPI", className='logo-mark'),
                html.Div("Analyse Financière", className='sidebar-title')
            ]),

            html.Div(className='sidebar-section', children=[
                html.Div("RÉFÉRENTIEL", className='sidebar-label'),
                dcc.RadioItems(
                    id='dataset-selector',
                    options=[
                        {'label': ' MQ (Management Quality)', 'value': 'mq'},
                        {'label': ' ACT (Transition Carbone)', 'value': 'act'},
                    ],
                    value='mq',
                    className='custom-radio'
                ),
            ]),

            html.Div(className='sidebar-section', children=[
                html.Div("NAVIGATION", className='sidebar-label'),
                dbc.Nav([
                    dbc.NavLink("Accueil",            href="/",           active="exact"),
                    dbc.NavLink("Fiche Société",       href="/societe",    active="exact"),
                    dbc.NavLink("Panel Quintiles",     href="/panel",      active="exact"),
                    dbc.NavLink("Analyse Stratégique", href="/strategique",active="exact"),
                    dbc.NavLink("Score Composite",     href="/composite",  active="exact"),
                    dbc.NavLink("Régression OLS",      href="/ols",        active="exact"),
                    dbc.NavLink("Impact Brent",        href="/brent",      active="exact"),
                ], vertical=True, pills=True),
            ]),

            html.Div(style={'marginTop': 'auto', 'padding': '20px'}, children=[
                html.Hr(style={'borderColor': '#30363d'}),
                html.A(
                    "Déconnexion", href="/logout",
                    className='logout-link',
                    style={'color': '#f85149', 'textDecoration': 'none', 'fontSize': '12px'}
                )
            ])
        ]),

        html.Div(className='main-content', id='page-content')
    ])


app.layout = serve_layout


# ── ROUTER ────────────────────────────────────────────────────────────────────
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'),
     Input('dataset-selector', 'value')]
)
def display_page(pathname, d_key):
    if not current_user.is_authenticated:
        return html.Div("Veuillez vous connecter...")

    if not APP_DATA:
        return html.Div("Erreur : Données non chargées.")

    ctx = {
        'valid':   APP_DATA[d_key]['valid'],
        'prices':  APP_DATA[d_key]['prices'],
        'brent':   APP_DATA['brent'],
        'rallies': APP_DATA['rallies'],
        'is_mq':   (d_key == 'mq'),
    }

    if pathname == '/societe':     return layout_societe(ctx)
    if pathname == '/panel':       return layout_panel(ctx)
    if pathname == '/brent':       return layout_brent(ctx)
    if pathname == '/ols':         return layout_ols(ctx)
    if pathname == '/strategique': return layout_strategique(ctx)
    if pathname == '/composite':   return layout_composite(ctx)

    return layout_accueil(ctx)


# ── ENREGISTREMENT DES CALLBACKS ──────────────────────────────────────────────
cb_societe(app, APP_DATA)
cb_brent(app, APP_DATA)
cb_ols(app, APP_DATA)
cb_strategique(app, APP_DATA)
cb_composite(app, APP_DATA)


# ── LANCEMENT ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
