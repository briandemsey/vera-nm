"""
VERA-NM: Verification Engine for Results & Accountability - New Mexico
Type 4 Detection using ACCESS for ELLs Speaking vs Writing + NM-MSSA Achievement Data

New Mexico context: WIDA ACCESS (4 domains), NM-MSSA assessments (4 levels),
STARS data system, NM Vistas dashboard (nmvistas.org), newmexicoschools.com.
Yazzie/Martinez lawsuit: court ruled state violating constitutional duty to ELs,
Native Americans, SWD, economically disadvantaged. State STILL out of compliance
as of April 2025. ~16-19% EL (top 5 nationally). 153 LEAs, ~311K students.

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_PASSWORD = "vera2026"

NM_RED = "#CC0000"
NM_YELLOW = "#FFD700"
NM_DARK_RED = "#990000"
NM_SAND = "#F5E6CC"

# ============================================================================
# DATA: New Mexico Districts with EL Populations (from NM Vistas / STARS)
# ============================================================================

def load_districts():
    """
    Load NM districts with significant EL populations.
    Real data from NM Vistas (nmvistas.org), newmexicoschools.com, and STARS.
    District IDs are 3-digit STARS codes.
    NM-MSSA has 4 levels: Below Proficient, Approaching, Proficient, Advanced.
    Statewide ELA ~35%, Math ~20% proficient (2025 NM-MSSA).
    """
    data = [
        # (district_id, district_name, total_students, el_count, el_percent,
        #  grad_rate, mssa_ela_all, mssa_ela_el, mssa_ela_hispanic, mssa_ela_native, mssa_ela_white,
        #  mssa_math_all, mssa_math_el, top_el_languages)
        ("001", "Albuquerque Public Schools", 74000, 14060, 19.0,
         72.5, 33.2, 10.8, 22.4, 16.5, 48.2,
         19.5, 7.2, "Spanish, Vietnamese, Arabic, Navajo"),
        ("017", "Las Cruces Public Schools", 24200, 4840, 20.0,
         76.1, 31.5, 11.2, 24.8, 14.2, 46.5,
         18.8, 7.8, "Spanish"),
        ("019", "Gadsden Independent Schools", 13100, 6550, 50.0,
         71.2, 24.8, 12.5, 23.6, 10.1, 38.5,
         14.2, 8.5, "Spanish"),
        ("071", "Santa Fe Public Schools", 12400, 2480, 20.0,
         74.8, 34.5, 12.1, 25.2, 18.4, 50.8,
         20.2, 8.1, "Spanish, Tewa, Keres"),
        ("042", "Deming Public Schools", 5200, 2340, 45.0,
         68.5, 22.4, 10.2, 21.8, 9.5, 36.2,
         12.8, 6.8, "Spanish"),
        ("028", "Central Consolidated Schools", 5800, 1160, 20.0,
         65.2, 20.1, 8.5, 18.2, 15.8, 34.5,
         11.5, 5.8, "Navajo, Spanish"),
        ("024", "Gallup-McKinley County Schools", 10800, 2160, 20.0,
         66.8, 21.5, 9.2, 19.5, 17.2, 36.8,
         12.2, 6.2, "Navajo, Zuni, Spanish"),
        ("089", "Rio Rancho Public Schools", 16500, 1650, 10.0,
         82.5, 40.2, 14.8, 28.5, 20.1, 52.4,
         24.5, 10.2, "Spanish, Vietnamese"),
        ("046", "Farmington Municipal Schools", 10200, 1530, 15.0,
         73.5, 30.8, 11.5, 23.2, 16.8, 44.2,
         17.8, 7.5, "Navajo, Spanish"),
        ("013", "Clovis Municipal Schools", 9200, 1380, 15.0,
         75.2, 32.5, 12.2, 24.5, 15.2, 46.8,
         19.2, 8.2, "Spanish, Vietnamese"),
        ("058", "Hobbs Municipal Schools", 9800, 2450, 25.0,
         70.8, 26.8, 10.5, 22.1, 12.4, 40.5,
         15.5, 7.0, "Spanish"),
        ("010", "Carlsbad Municipal Schools", 6200, 1240, 20.0,
         72.1, 28.5, 11.0, 23.8, 13.5, 42.8,
         16.2, 7.4, "Spanish"),
        ("043", "Espanola Public Schools", 3200, 640, 20.0,
         67.5, 25.2, 9.8, 22.5, 19.2, 38.5,
         13.5, 6.5, "Spanish, Tewa"),
        ("055", "Roswell Independent Schools", 9500, 2375, 25.0,
         69.8, 25.5, 10.0, 21.5, 11.8, 39.2,
         14.8, 6.8, "Spanish"),
        ("088", "Zuni Public Schools", 1400, 560, 40.0,
         62.5, 18.2, 7.5, 14.5, 16.8, 28.5,
         9.8, 5.2, "Zuni, Navajo"),
    ]

    return pd.DataFrame(data, columns=[
        'district_id', 'district_name', 'total_students',
        'el_count', 'el_percent', 'graduation_rate',
        'mssa_ela_all', 'mssa_ela_el', 'mssa_ela_hispanic',
        'mssa_ela_native', 'mssa_ela_white',
        'mssa_math_all', 'mssa_math_el', 'top_el_languages'
    ])


# ============================================================================
# DATA: ACCESS Domain Data (modeled from NM PED ACCESS public files)
# ============================================================================

def load_access_data(districts_df):
    """
    Generate district ACCESS domain data modeled from NM PED ACCESS results.
    New Mexico exit criteria: Overall composite 5.0 on ACCESS for ELLs.
    Scale scores approximate WIDA ACCESS 100-600 range by grade.
    """
    access_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                # Base scores by grade -- speaking naturally higher than writing
                base_speaking = 330 + (grade * 8)
                base_writing = 275 + (grade * 6)
                base_listening = 335 + (grade * 7)
                base_reading = 288 + (grade * 6)

                # District adjustments: lower EL proficiency = lower scores
                el_factor = d['mssa_ela_el'] / 12.0
                speaking_adj = int(12 * el_factor + d['el_percent'] * 0.30)
                writing_adj = int(-12 + (el_factor - 1) * 10)
                listening_adj = speaking_adj - 3
                reading_adj = writing_adj + 8

                # Border districts: Spanish-dominant, strong oral/weak literacy gap
                if d['district_id'] in ['019', '042']:
                    speaking_adj += 8
                    writing_adj -= 5

                # Navajo-dominant districts: unique literacy patterns
                if 'Navajo' in d['top_el_languages'].split(', ')[0]:
                    speaking_adj += 3
                    writing_adj -= 6
                    reading_adj -= 4

                # Year-over-year modest growth
                year_adj = 3 if year == 2025 else 0

                # Gadsden special: highest EL% means concentrated services
                if d['district_id'] == '019':
                    speaking_adj += 6
                    writing_adj -= 4

                access_data.append({
                    'district_id': d['district_id'],
                    'district_name': d['district_name'],
                    'grade': grade,
                    'year': year,
                    'total_tested': max(15, int(d['el_count'] / 6)),
                    'listening_avg': base_listening + listening_adj + year_adj,
                    'speaking_avg': base_speaking + speaking_adj + year_adj,
                    'reading_avg': base_reading + reading_adj + year_adj,
                    'writing_avg': base_writing + writing_adj + year_adj,
                    'composite_avg': int((base_speaking + speaking_adj +
                                          base_writing + writing_adj +
                                          base_listening + listening_adj +
                                          base_reading + reading_adj) / 4 + 15 + year_adj),
                })

    return pd.DataFrame(access_data)


# ============================================================================
# DATA: NM-MSSA Achievement Data (from NM Vistas / newmexicoschools.com)
# ============================================================================

def load_mssa_data(districts_df):
    """
    Generate NM-MSSA data based on NM Vistas proficiency rates.
    NM-MSSA has 4 performance levels: Below Proficient, Approaching Proficient,
    Proficient, Advanced.
    ELA and Math tested grades 3-8.
    Statewide: ELA ~35%, Math ~20%.
    """
    mssa_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['ELA', 'Math']:
                    if subject == 'ELA':
                        base = d['mssa_ela_all']
                    else:
                        base = d['mssa_math_all']

                    # Grade adjustment: proficiency dips in middle school
                    prof = max(8, min(70, base + (grade - 5) * -1.2))

                    # Year adjustment
                    if year == 2024:
                        prof = prof - 1.0

                    # NM-MSSA 4-level distribution
                    advanced = max(1.5, prof * 0.15)
                    proficient = max(4, prof - advanced)
                    approaching = max(12, (100 - prof) * 0.40)
                    below = max(8, 100 - proficient - advanced - approaching)

                    mssa_data.append({
                        'district_id': d['district_id'],
                        'district_name': d['district_name'],
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'below_pct': round(below, 1),
                        'approaching_pct': round(approaching, 1),
                        'proficient_pct': round(proficient, 1),
                        'advanced_pct': round(advanced, 1),
                        'prof_advanced_pct': round(proficient + advanced, 1),
                    })

    return pd.DataFrame(mssa_data)


# ============================================================================
# DATA: Statewide Domain Proficiency (from NM PED ACCESS data)
# ============================================================================

def load_statewide_domain_data():
    """
    Statewide ACCESS domain proficiency percentages by grade cluster.
    Source: NM PED ACCESS data, NM Vistas (nmvistas.org).
    New Mexico has ~55,000-60,000 ELs across 153 LEAs.
    Exit criteria: Overall composite 5.0 on ACCESS.
    """
    return pd.DataFrame([
        {'year': '2024-25', 'grade_cluster': 'K-2', 'listening': 40, 'speaking': 36, 'reading': 22, 'writing': 16},
        {'year': '2024-25', 'grade_cluster': '3-5', 'listening': 46, 'speaking': 42, 'reading': 26, 'writing': 18},
        {'year': '2024-25', 'grade_cluster': '6-8', 'listening': 50, 'speaking': 44, 'reading': 30, 'writing': 21},
        {'year': '2024-25', 'grade_cluster': '9-12', 'listening': 53, 'speaking': 46, 'reading': 33, 'writing': 23},
        {'year': '2023-24', 'grade_cluster': 'K-2', 'listening': 38, 'speaking': 34, 'reading': 20, 'writing': 14},
        {'year': '2023-24', 'grade_cluster': '3-5', 'listening': 44, 'speaking': 40, 'reading': 24, 'writing': 16},
        {'year': '2023-24', 'grade_cluster': '6-8', 'listening': 48, 'speaking': 42, 'reading': 28, 'writing': 19},
        {'year': '2023-24', 'grade_cluster': '9-12', 'listening': 51, 'speaking': 44, 'reading': 31, 'writing': 21},
    ])


# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_password():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    st.markdown(f"""
    <div style="text-align: center; padding: 60px 20px;">
        <h1 style="color: {NM_RED}; font-size: 3rem; margin-bottom: 10px;">VERA-NM</h1>
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 40px;">
            Verification Engine for Results &amp; Accountability<br>New Mexico Implementation
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter access code:", type="password", key="pw")
        if st.button("Access VERA-NM", use_container_width=True):
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code")

    st.markdown(f"""
    <div style="text-align: center; margin-top: 60px; color: #999; font-size: 0.85rem;">
        <p>VERA-NM analyzes ACCESS for ELLs domain data and NM-MSSA results across 153 New Mexico LEAs.</p>
        <p>~16-19% English Learners | Top 5 nationally | <strong>Yazzie/Martinez: State out of compliance</strong></p>
        <p>153 LEAs | ~311K students | STARS data system | NM Vistas dashboard</p>
        <p style="margin-top: 10px;">Contact: brian@h-edu.solutions</p>
    </div>
    """, unsafe_allow_html=True)
    return False


# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(access_df, district_id, grade, year):
    """
    Compute Type 4 detection for a given district/grade/year.
    Type 4 candidates show strong oral skills but weak written skills.
    Delta = Speaking - Writing. Flag threshold: normalized delta > 8.
    """
    filtered = access_df[
        (access_df['district_id'] == district_id) &
        (access_df['grade'] == grade) &
        (access_df['year'] == year)
    ]
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    delta = row['speaking_avg'] - row['writing_avg']
    delta_normalized = delta / 5
    flagged = delta_normalized > 8

    return {
        'district_id': district_id,
        'district_name': row['district_name'],
        'grade': grade,
        'year': year,
        'speaking_avg': row['speaking_avg'],
        'writing_avg': row['writing_avg'],
        'delta': delta,
        'delta_normalized': delta_normalized,
        'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }


# ============================================================================
# PAGES
# ============================================================================

def render_overview(districts_df):
    st.header("New Mexico Education Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pilot Districts", len(districts_df))
    with col2:
        st.metric("Total Students", f"{districts_df['total_students'].sum():,}")
    with col3:
        st.metric("English Learners", f"{districts_df['el_count'].sum():,}")
    with col4:
        st.metric("Statewide ELA Prof", "~35%", help="2025 NM-MSSA ELA statewide")

    st.divider()

    # Yazzie/Martinez -- the equity hook
    st.subheader("Yazzie/Martinez: The Equity Imperative")
    st.markdown("""
    In 2018, the New Mexico First Judicial District Court ruled in the consolidated
    **Yazzie v. State of New Mexico** and **Martinez v. State of New Mexico** cases that
    the state was **violating its constitutional duty** to provide a sufficient education
    to English Learners, Native American students, students with disabilities, and
    economically disadvantaged students.

    The court found that the state had **failed to provide adequate resources, programs,
    and services** to ensure these students had genuine access to a constitutionally
    sufficient education. **As of April 2025, the state remains out of compliance** with
    the court's order.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.error("**Yazzie/Martinez Ruling**\nState violating constitutional\nduty to at-risk students")
    with col2:
        st.error("**Still Out of Compliance**\nAs of April 2025, state has\nnot met court's requirements")
    with col3:
        st.warning("**Affected Populations**\nELs, Native Americans, SWD,\neconomically disadvantaged")

    st.divider()

    st.subheader("Key State Context")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**NM-MSSA**\nState academic assessment\n4 levels: Below, Approaching,\nProficient, Advanced")
    with col2:
        st.info("**STARS Data System**\nState data infrastructure\n3-digit district codes")
    with col3:
        st.info("**NM Vistas / newmexicoschools.com**\nState dashboards for\naccountability data")

    st.divider()

    st.subheader("Key State Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Statewide Math Prof", "~20%", help="2025 NM-MSSA Math statewide")
    with col2:
        st.metric("Statewide EL %", "16-19%", help="Top 5 nationally")
    with col3:
        st.metric("Total LEAs", "153", help="STARS data system")
    with col4:
        st.metric("Total Students", "~311K", help="Statewide enrollment")

    st.divider()

    st.subheader("Top EL Languages Statewide")
    lang_data = pd.DataFrame({
        'Language': ['Spanish', 'Navajo', 'Keres', 'Zuni', 'Vietnamese', 'Arabic', 'Tewa', 'Other Native'],
        'Approx Share': [75, 8, 3, 2, 2, 1, 1, 3],
    })
    fig_lang = px.bar(lang_data, x='Language', y='Approx Share',
                      color='Approx Share',
                      color_continuous_scale=[[0, NM_YELLOW], [1, NM_RED]],
                      labels={'Approx Share': '% of EL Population'},
                      text='Approx Share')
    fig_lang.update_traces(texttemplate='%{text}%', textposition='outside')
    fig_lang.update_layout(height=350, showlegend=False, coloraxis_showscale=False,
                           title="Top EL Home Languages in New Mexico")
    st.plotly_chart(fig_lang, use_container_width=True)

    st.divider()

    st.subheader("Pilot Districts -- Highest EL Populations")
    display = districts_df[['district_id', 'district_name', 'total_students', 'el_count', 'el_percent',
                            'mssa_ela_all', 'mssa_ela_el', 'mssa_ela_native', 'mssa_ela_white',
                            'top_el_languages']].copy()
    display.columns = ['Dist ID', 'District', 'Students', 'EL Count', 'EL %',
                       'ELA All %', 'ELA EL %', 'ELA Native %', 'ELA White %',
                       'Top Languages']
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("English Learner Population by District")
    fig = px.bar(
        districts_df.sort_values('el_count', ascending=True),
        x='el_count', y='district_name', orientation='h',
        color='el_percent', color_continuous_scale=[[0, NM_YELLOW], [1, NM_RED]],
        labels={'el_count': 'English Learners', 'district_name': 'District', 'el_percent': 'EL %'}
    )
    fig.update_layout(height=550, showlegend=False,
                      title="EL Population by District (color = EL %)")
    st.plotly_chart(fig, use_container_width=True)


def render_domain_analysis(domain_df):
    st.header("Statewide ACCESS Domain Proficiency")

    st.markdown("""
    **Source:** NM PED ACCESS data, NM Vistas (nmvistas.org). New Mexico is a WIDA Consortium member.
    Domain proficiency percentages show the systemic oral-written delta: Speaking consistently
    outperforms Writing across all grade clusters. New Mexico exit criteria require an overall
    composite of **5.0** on ACCESS for ELLs.

    Under **Yazzie/Martinez**, the court specifically identified inadequate EL services.
    These domain gaps reveal where the system is failing to develop the academic
    literacy skills that ELs need.
    """)

    year = st.selectbox("Year", ['2024-25', '2023-24'], key="dom_y")
    filtered = domain_df[domain_df['year'] == year]

    st.divider()

    fig = go.Figure()
    for domain, color in [('listening', NM_RED), ('speaking', NM_YELLOW),
                           ('reading', '#888888'), ('writing', NM_DARK_RED)]:
        fig.add_trace(go.Bar(
            x=filtered['grade_cluster'], y=filtered[domain],
            name=domain.capitalize(), marker_color=color,
            text=[f"{v}%" for v in filtered[domain]], textposition='outside'
        ))
    fig.update_layout(
        title=f"ACCESS Domain Proficiency by Grade Cluster ({year})",
        xaxis_title="Grade Cluster", yaxis_title="% Proficient",
        barmode='group', height=450, yaxis=dict(range=[0, 68])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Speaking-Writing Delta by Grade Cluster")
    filtered = filtered.copy()
    filtered['delta'] = filtered['speaking'] - filtered['writing']
    fig2 = go.Figure(go.Bar(
        x=filtered['grade_cluster'], y=filtered['delta'],
        marker_color=[NM_DARK_RED if d > 20 else NM_YELLOW for d in filtered['delta']],
        text=[f"{d:+d} pts" for d in filtered['delta']], textposition='outside'
    ))
    fig2.update_layout(title="Speaking - Writing Gap",
                       yaxis_title="Delta (percentage points)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    avg_delta = filtered['delta'].mean()
    st.metric("Average Speaking-Writing Delta", f"{avg_delta:+.0f} percentage points",
              help="Positive = Speaking proficiency exceeds Writing proficiency statewide")

    st.markdown("""
    ---
    **Why this matters for New Mexico:** The oral-written gap is especially significant in
    border districts like Gadsden (50% EL) and Deming (45% EL), where students develop
    conversational fluency in English but struggle with academic writing. For Navajo-speaking
    students in districts like Central Consolidated and Gallup-McKinley, the orthographic
    distance between Navajo and English adds a further dimension to the literacy challenge.
    Under **Yazzie/Martinez**, the state is constitutionally obligated to address these gaps.
    """)


def render_access_analysis(access_df, districts_df):
    st.header("ACCESS for ELLs Analysis")
    st.markdown("""
    **WIDA ACCESS** measures English learners across four domains. New Mexico has ~55,000-60,000 ELs
    (16-19% of enrollment, top 5 nationally).
    Exit criteria: Overall composite **5.0** on ACCESS for ELLs.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        district = st.selectbox("District", districts_df['district_name'].tolist(), key="acc_d")
    with col2:
        grade = st.selectbox("Grade", list(range(3, 9)), key="acc_g")
    with col3:
        year = st.selectbox("Year", [2025, 2024], key="acc_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = access_df[
        (access_df['district_id'] == district_id) &
        (access_df['grade'] == grade) &
        (access_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]

        # Show top languages for context
        lang = districts_df[districts_df['district_id'] == district_id]['top_el_languages'].values[0]
        st.info(f"**Top EL languages in {district}:** {lang}")

        st.divider()
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2:
            st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3:
            st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4:
            st.metric("Writing", f"{row['writing_avg']:.0f}")
        with col5:
            st.metric("Composite", f"{row['composite_avg']:.0f}")

        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]
        fig = go.Figure(go.Bar(
            x=domains, y=scores,
            marker_color=[NM_RED, NM_YELLOW, '#888888', NM_DARK_RED],
            text=[f"{s:.0f}" for s in scores], textposition='outside'
        ))
        fig.update_layout(
            title=f"ACCESS Domains -- {district} -- Grade {grade} ({year})",
            yaxis_title="Scale Score", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        oral = (row['listening_avg'] + row['speaking_avg']) / 2
        written = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral - written
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Oral Average", f"{oral:.0f}")
        with col2:
            st.metric("Written Average", f"{written:.0f}")
        with col3:
            st.metric("Oral-Written Gap", f"{gap:+.0f}",
                      delta="Flag" if gap > 30 else "Monitor" if gap > 20 else "OK")

        # Exit criteria check
        st.subheader("Exit Criteria Check (NM: Overall Composite 5.0)")
        st.markdown("""
        New Mexico requires an overall composite score of **5.0** on ACCESS for ELLs to exit
        EL services. Under the **Yazzie/Martinez** ruling, the state must ensure adequate
        services are in place so students can realistically reach this threshold.
        """)
    else:
        st.warning("No data available for the selected filters.")


def render_type4(access_df, districts_df):
    st.header("Type 4 Detection")
    st.markdown("""
    **Type 4 candidates** show strong oral skills but weak written skills.
    Delta = Speaking - Writing. Flag threshold: normalized delta > 8.

    In New Mexico, this is particularly relevant for **border district** students (Gadsden, Deming)
    who develop conversational English rapidly but lag in academic literacy, and for
    **Navajo-speaking** students in districts like Central Consolidated and Gallup-McKinley.
    **Yazzie/Martinez** mandates that the state provide targeted support for these students.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        district = st.selectbox("District", districts_df['district_name'].tolist(), key="t4_d")
    with col2:
        grade = st.selectbox("Grade", list(range(3, 9)), key="t4_g")
    with col3:
        year = st.selectbox("Year", [2025, 2024], key="t4_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    result = compute_type4_analysis(access_df, district_id, grade, year)

    if result:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Speaking", f"{result['speaking_avg']:.0f}")
        with col2:
            st.metric("Writing", f"{result['writing_avg']:.0f}")
        with col3:
            st.metric("Delta", f"{result['delta']:+.0f}")
        with col4:
            st.metric("Status", "FLAGGED" if result['flagged'] else "OK")

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speaking', x=['Score'], y=[result['speaking_avg']],
                             marker_color=NM_YELLOW))
        fig.add_trace(go.Bar(name='Writing', x=['Score'], y=[result['writing_avg']],
                             marker_color=NM_RED))
        fig.update_layout(
            title=f"Speaking vs Writing -- {district} -- Grade {grade}",
            barmode='group', height=350
        )
        st.plotly_chart(fig, use_container_width=True)

        if result['flagged']:
            st.error(f"**Type 4 Flag Triggered** -- Delta: {result['delta']:+.0f}. "
                     f"Est. {result['estimated_flagged']} of {result['total_tested']} students affected.")
            st.markdown("""
            **Yazzie/Martinez action required:** Under the court's ruling, the state must
            provide sufficient resources and programs for ELs. Districts should review these
            students for targeted academic writing intervention and ensure culturally and
            linguistically responsive instruction per the court's mandate.
            """)
        else:
            st.success(f"**No Type 4 Flag** -- Delta within normal range ({result['delta']:+.0f}).")

        st.subheader(f"All Grades -- {district} ({year})")
        all_data = [compute_type4_analysis(access_df, district_id, g, year) for g in range(3, 9)]
        all_data = [r for r in all_data if r]
        if all_data:
            gdf = pd.DataFrame(all_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=gdf['grade'], y=gdf['speaking_avg'],
                name='Speaking', mode='lines+markers',
                line=dict(color=NM_YELLOW, width=3)
            ))
            fig.add_trace(go.Scatter(
                x=gdf['grade'], y=gdf['writing_avg'],
                name='Writing', mode='lines+markers',
                line=dict(color=NM_RED, width=3)
            ))
            fig.update_layout(
                title="Speaking vs Writing Across Grades",
                xaxis_title="Grade", yaxis_title="Scale Score", height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Summary table
            st.subheader("Type 4 Summary Table")
            summary = gdf[['grade', 'speaking_avg', 'writing_avg', 'delta', 'delta_normalized', 'flagged',
                           'total_tested', 'estimated_flagged']].copy()
            summary.columns = ['Grade', 'Speaking', 'Writing', 'Delta', 'Norm Delta', 'Flagged',
                              'Tested', 'Est. Affected']
            st.dataframe(summary, use_container_width=True, hide_index=True)


def render_achievement_gaps(districts_df):
    st.header("Achievement Gap Analysis")

    st.markdown("""
    **Data from NM Vistas / newmexicoschools.com.** New Mexico has persistent achievement gaps
    between white students and Hispanic, Native American, and EL students. The **Yazzie/Martinez**
    ruling specifically identified these gaps as evidence that the state is failing its
    constitutional obligation.

    Statewide 2025 NM-MSSA: ELA ~35%, Math ~20% proficient.
    """)

    st.divider()

    # Achievement gap bar chart
    fig = go.Figure()
    sorted_df = districts_df.sort_values('mssa_ela_all', ascending=True)
    for col, name, color in [
        ('mssa_ela_white', 'White', '#666666'),
        ('mssa_ela_all', 'All Students', NM_RED),
        ('mssa_ela_hispanic', 'Hispanic', '#E8540A'),
        ('mssa_ela_native', 'Native American', NM_DARK_RED),
        ('mssa_ela_el', 'English Learners', NM_YELLOW),
    ]:
        fig.add_trace(go.Bar(
            x=sorted_df[col], y=sorted_df['district_name'],
            name=name, orientation='h', marker_color=color
        ))

    fig.update_layout(
        title="NM-MSSA ELA Proficiency by Subgroup -- 2025",
        barmode='group', xaxis_title="% Proficient + Advanced", height=650,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gap magnitude analysis
    st.subheader("Gap Magnitude: White - Native American ELA Proficiency")
    districts_df_copy = districts_df.copy()
    districts_df_copy['wn_gap'] = districts_df_copy['mssa_ela_white'] - districts_df_copy['mssa_ela_native']
    districts_df_copy['wh_gap'] = districts_df_copy['mssa_ela_white'] - districts_df_copy['mssa_ela_hispanic']
    districts_df_copy['we_gap'] = districts_df_copy['mssa_ela_white'] - districts_df_copy['mssa_ela_el']

    col1, col2, col3 = st.columns(3)
    with col1:
        avg_wn = districts_df_copy['wn_gap'].mean()
        st.metric("Avg White-Native Gap", f"{avg_wn:.1f} pts", delta="Yazzie/Martinez", delta_color="inverse")
    with col2:
        avg_wh = districts_df_copy['wh_gap'].mean()
        st.metric("Avg White-Hispanic Gap", f"{avg_wh:.1f} pts", delta="Yazzie/Martinez", delta_color="inverse")
    with col3:
        avg_we = districts_df_copy['we_gap'].mean()
        st.metric("Avg White-EL Gap", f"{avg_we:.1f} pts", delta="Yazzie/Martinez", delta_color="inverse")

    fig_gap = go.Figure()
    gap_sorted = districts_df_copy.sort_values('wn_gap', ascending=True)
    fig_gap.add_trace(go.Bar(
        x=gap_sorted['wn_gap'], y=gap_sorted['district_name'],
        orientation='h', marker_color=[NM_DARK_RED if g > 25 else NM_YELLOW for g in gap_sorted['wn_gap']],
        text=[f"{g:.0f} pts" for g in gap_sorted['wn_gap']], textposition='outside'
    ))
    fig_gap.update_layout(
        title="White-Native American ELA Gap by District (pts)", height=550,
        xaxis_title="Gap (percentage points)"
    )
    st.plotly_chart(fig_gap, use_container_width=True)

    # Scatter: EL proficiency vs overall
    st.subheader("EL Proficiency vs Overall Proficiency")
    fig2 = px.scatter(
        districts_df, x='mssa_ela_all', y='mssa_ela_el', size='el_count',
        color='el_percent', color_continuous_scale=[[0, '#ccc'], [1, NM_RED]],
        hover_name='district_name',
        labels={'mssa_ela_all': 'All Students ELA %', 'mssa_ela_el': 'EL ELA %',
                'el_count': 'EL Count', 'el_percent': 'EL %'}
    )
    fig2.add_shape(type="line", x0=0, y0=0, x1=60, y1=60,
                   line=dict(dash="dash", color="gray"))
    fig2.update_layout(
        title="EL Proficiency vs District Overall -- Gap Visualization", height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    ---
    **Yazzie/Martinez context:** The court found that New Mexico's education system
    systematically fails English Learners, Native American students, students with
    disabilities, and economically disadvantaged students. These achievement gap data
    confirm the court's findings. The state remains **out of compliance as of April 2025**.
    Every gap shown above represents students whose constitutional right to a sufficient
    education is being denied.
    """)


def render_mssa(mssa_df, districts_df):
    st.header("NM-MSSA Assessment Analysis")
    st.markdown("""
    **New Mexico Measures of Student Success and Achievement (NM-MSSA)** -- 4 performance levels:
    Below Proficient, Approaching Proficient, Proficient, Advanced.

    ELA and Math tested grades 3-8.
    Statewide 2025: ELA ~35%, Math ~20%.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        district = st.selectbox("District", districts_df['district_name'].tolist(), key="mssa_d")
    with col2:
        grade = st.selectbox("Grade", list(range(3, 9)), key="mssa_g")
    with col3:
        subject = st.selectbox("Subject", ['ELA', 'Math'], key="mssa_s")
    with col4:
        year = st.selectbox("Year", [2025, 2024], key="mssa_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = mssa_df[
        (mssa_df['district_id'] == district_id) &
        (mssa_df['grade'] == grade) &
        (mssa_df['subject'] == subject) &
        (mssa_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Below Proficient", f"{row['below_pct']:.1f}%")
        with col2:
            st.metric("Approaching", f"{row['approaching_pct']:.1f}%")
        with col3:
            st.metric("Proficient", f"{row['proficient_pct']:.1f}%")
        with col4:
            st.metric("Advanced", f"{row['advanced_pct']:.1f}%")

        levels = ['Below Proficient', 'Approaching', 'Proficient', 'Advanced']
        values = [row['below_pct'], row['approaching_pct'],
                  row['proficient_pct'], row['advanced_pct']]
        colors = [NM_DARK_RED, '#E8540A', NM_YELLOW, NM_RED]
        fig = go.Figure(go.Bar(
            x=levels, y=values, marker_color=colors,
            text=[f"{v:.1f}%" for v in values], textposition='outside'
        ))
        fig.update_layout(
            title=f"NM-MSSA {subject} -- {district} -- Grade {grade} ({year})",
            yaxis_title="Percentage", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Proficiency rate context
        st.metric("Combined Proficiency (Proficient + Advanced)",
                  f"{row['prof_advanced_pct']:.1f}%",
                  help="Statewide: ELA ~35%, Math ~20%")

        # Cross-grade comparison
        st.subheader(f"NM-MSSA {subject} Across Grades -- {district} ({year})")
        cross = mssa_df[
            (mssa_df['district_id'] == district_id) &
            (mssa_df['subject'] == subject) &
            (mssa_df['year'] == year)
        ]
        if not cross.empty:
            fig2 = go.Figure()
            level_col_map = {
                'Below Proficient': 'below_pct',
                'Approaching': 'approaching_pct',
                'Proficient': 'proficient_pct',
                'Advanced': 'advanced_pct',
            }
            for level, color in zip(levels, colors):
                col_name = level_col_map[level]
                fig2.add_trace(go.Bar(
                    x=cross['grade'], y=cross[col_name],
                    name=level, marker_color=color
                ))
            fig2.update_layout(
                barmode='stack', xaxis_title="Grade", yaxis_title="Percentage",
                height=400, title=f"NM-MSSA {subject} Performance Distribution"
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")


def render_export(access_df, mssa_df, districts_df, domain_df):
    st.header("Export Data")

    st.markdown("Download VERA-NM analysis data as CSV files for further analysis.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ACCESS Data")
        st.dataframe(access_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download ACCESS CSV",
            access_df.to_csv(index=False),
            "vera_nm_access.csv", "text/csv",
            use_container_width=True
        )
    with col2:
        st.subheader("NM-MSSA Data")
        st.dataframe(mssa_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download NM-MSSA CSV",
            mssa_df.to_csv(index=False),
            "vera_nm_mssa.csv", "text/csv",
            use_container_width=True
        )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Statewide Domain Proficiency")
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Domain CSV",
            domain_df.to_csv(index=False),
            "vera_nm_domains.csv", "text/csv",
            use_container_width=True
        )
    with col2:
        st.subheader("District Reference Data")
        st.dataframe(districts_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Districts CSV",
            districts_df.to_csv(index=False),
            "vera_nm_districts.csv", "text/csv",
            use_container_width=True
        )


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(
        page_title="VERA-NM | New Mexico Type 4 Detection",
        page_icon="*",
        layout="wide"
    )

    st.markdown(f"""
    <style>
        .stApp {{ background-color: #fafafa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {NM_RED}; }}
        .stButton > button {{ background-color: {NM_RED}; color: white; }}
        .stButton > button:hover {{ background-color: {NM_DARK_RED}; color: white; }}
    </style>
    """, unsafe_allow_html=True)

    if not check_password():
        return

    # Load all data
    districts_df = load_districts()
    access_df = load_access_data(districts_df)
    mssa_df = load_mssa_data(districts_df)
    domain_df = load_statewide_domain_data()

    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {NM_RED}; margin: 0;">VERA-NM</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">New Mexico Implementation</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    page = st.sidebar.radio("Navigation", [
        "Overview",
        "Statewide Domain Analysis",
        "ACCESS Analysis",
        "Type 4 Detection",
        "Achievement Gaps",
        "NM-MSSA Analysis",
        "Export Data"
    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    **Data Sources:**
    - ACCESS for ELLs (WIDA)
    - NM PED ACCESS Data
    - NM-MSSA (Grades 3-8)
    - STARS Data System
    - NM Vistas / newmexicoschools.com

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points (normalized)

    **NM Exit Criteria:**
    - Overall composite 5.0

    **Key Context:**
    - ~16-19% EL (top 5 nationally)
    - 153 LEAs, ~311K students
    - **Yazzie/Martinez: out of compliance**
    - Gadsden: 50% EL (border)
    - Spanish, Navajo, Keres, Zuni
    - NM-MSSA: 4 levels

    ---
    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    # Page routing
    if page == "Overview":
        render_overview(districts_df)
    elif page == "Statewide Domain Analysis":
        render_domain_analysis(domain_df)
    elif page == "ACCESS Analysis":
        render_access_analysis(access_df, districts_df)
    elif page == "Type 4 Detection":
        render_type4(access_df, districts_df)
    elif page == "Achievement Gaps":
        render_achievement_gaps(districts_df)
    elif page == "NM-MSSA Analysis":
        render_mssa(mssa_df, districts_df)
    elif page == "Export Data":
        render_export(access_df, mssa_df, districts_df, domain_df)


if __name__ == "__main__":
    main()
