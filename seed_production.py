"""Production-grade seed script for DiligentEdu.

Wipes ALL seeded data and re-seeds with realistic, class-appropriate NCERT content.
- Class 9 students ONLY get Class 9 Science + Math content
- Class 10 students ONLY get Class 10 Science + Math content
- 15-30 quizzes per student across both subjects
- Realistic question text, correct/wrong answer patterns, concept IDs
- Teacher action plans, study twin matches, uploaded documents
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import execute_values

# ---------------------------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_PcXlwv4ht3In@ep-lively-lake-azz6bgwh-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require",
)


def get_conn():
    return psycopg2.connect(DATABASE_URL)


# ---------------------------------------------------------------------------
# CURRICULUM DATA — NCERT Class 9 & 10 (Science + Mathematics)
# ---------------------------------------------------------------------------

CLASS_9_SCIENCE = [
    {
        "chapter": "Exploration: Entering the World of Secondary Science",
        "chapter_number": 1,
        "concepts": [
            "sci9_ch1_scientific_method",
            "sci9_ch1_measurement_units",
            "sci9_ch1_lab_safety",
        ],
    },
    {
        "chapter": "Cell: The Building Block of Life",
        "chapter_number": 2,
        "concepts": ["cell9_structure", "cell9_organelles", "cell9_plant_animal_diff"],
    },
    {
        "chapter": "Tissues in Action",
        "chapter_number": 3,
        "concepts": [
            "tissue9_epithelial",
            "tissue9_connective",
            "tissue9_muscular",
            "tissue9_nervous",
        ],
    },
    {
        "chapter": "Describing Motion Around Us",
        "chapter_number": 4,
        "concepts": [
            "motion9_distance_displacement",
            "motion9_speed_velocity",
            "motion9_acceleration",
            "motion9_graphical_representation",
            "motion9_equations_of_motion",
        ],
    },
    {
        "chapter": "Exploring Mixtures and their Separation",
        "chapter_number": 5,
        "concepts": [
            "sci9_ch5_types_of_mixtures",
            "sci9_ch5_separation_techniques",
            "sci9_ch5_solution_properties",
        ],
    },
    {
        "chapter": "How Forces Affect Motion",
        "chapter_number": 6,
        "concepts": [
            "force9_balanced_unbalanced",
            "force9_newtons_laws",
            "force9_inertia",
            "force9_momentum",
            "force9_conservation_momentum",
        ],
    },
    {
        "chapter": "Work, Energy, and Simple Machines",
        "chapter_number": 7,
        "concepts": [
            "energy9_work_definition",
            "energy9_kinetic_potential",
            "energy9_conservation",
            "energy9_power",
            "energy9_simple_machines",
        ],
    },
    {
        "chapter": "Journey Inside the Atom",
        "chapter_number": 8,
        "concepts": [
            "sci9_ch8_atomic_models",
            "sci9_ch8_subatomic_particles",
            "sci9_ch8_electronic_configuration",
        ],
    },
    {
        "chapter": "Atomic Foundations of Matter",
        "chapter_number": 9,
        "concepts": [
            "sci9_ch9_atoms_molecules",
            "sci9_ch9_atomic_mass",
            "sci9_ch9_mole_concept",
            "sci9_ch9_chemical_formulae",
        ],
    },
    {
        "chapter": "Sound Waves: Characteristics and Applications",
        "chapter_number": 10,
        "concepts": [
            "sci9_ch10_production_propagation",
            "sci9_ch10_characteristics",
            "sci9_ch10_reflection_echo",
            "sci9_ch10_ultrasound_sonar",
        ],
    },
    {
        "chapter": "Reproduction: How Life Continues",
        "chapter_number": 11,
        "concepts": [
            "sci9_ch11_asexual_reproduction",
            "sci9_ch11_sexual_reproduction",
            "sci9_ch11_pollination",
        ],
    },
    {
        "chapter": "Patterns in Life: Diversity and Classification",
        "chapter_number": 12,
        "concepts": [
            "sci9_ch12_basis_of_classification",
            "sci9_ch12_plant_kingdom_divisions",
            "sci9_ch12_invertebrate_phyla",
            "sci9_ch12_chordata_vertebrates",
        ],
    },
    {
        "chapter": "Earth as a System: Energy, Matter, and Life",
        "chapter_number": 13,
        "concepts": [
            "sci9_ch13_atmosphere_climate",
            "sci9_ch13_biogeochemical_cycles",
            "sci9_ch13_greenhouse_ozone",
            "sci9_ch13_water_soil_resources",
        ],
    },
]

CLASS_9_MATH = [
    {
        "chapter": "Orienting Yourself: The Use of Coordinates",
        "chapter_number": 1,
        "concepts": [
            "math9_ch1_cartesian_plane",
            "math9_ch1_plotting_points",
            "math9_ch1_quadrants",
        ],
    },
    {
        "chapter": "Introduction to Linear Polynomials",
        "chapter_number": 2,
        "concepts": [
            "math9_ch2_polynomial_definition",
            "math9_ch2_zeroes_of_polynomial",
            "math9_ch2_remainder_theorem",
        ],
    },
    {
        "chapter": "The World of Numbers",
        "chapter_number": 3,
        "concepts": [
            "math9_ch3_number_systems",
            "math9_ch3_rational_irrational",
            "math9_ch3_laws_of_exponents",
        ],
    },
    {
        "chapter": "Exploring Algebraic Identities",
        "chapter_number": 4,
        "concepts": [
            "math9_ch4_standard_identities",
            "math9_ch4_factorisation",
            "math9_ch4_expansion",
        ],
    },
    {
        "chapter": "I'm Up and Down, and Round and Round",
        "chapter_number": 5,
        "concepts": [
            "math9_ch5_linear_equations",
            "math9_ch5_graphing_lines",
            "math9_ch5_geometric_shapes",
        ],
    },
    {
        "chapter": "Measuring Space: Perimeter and Area",
        "chapter_number": 6,
        "concepts": [
            "math9_ch6_herons_formula",
            "math9_ch6_area_triangle",
            "math9_ch6_area_quadrilateral",
        ],
    },
    {
        "chapter": "The Mathematics of Maybe: Introduction to Probability",
        "chapter_number": 7,
        "concepts": [
            "math9_ch7_experimental_probability",
            "math9_ch7_events_outcomes",
            "math9_ch7_probability_applications",
        ],
    },
    {
        "chapter": "Predicting What Comes Next: Exploring Sequences and Progressions",
        "chapter_number": 8,
        "concepts": [
            "math9_ch8_sequences",
            "math9_ch8_arithmetic_progression",
            "math9_ch8_common_difference",
        ],
    },
]

CLASS_10_SCIENCE = [
    {
        "chapter": "Chemical Reactions and Equations",
        "chapter_number": 1,
        "concepts": [
            "chem_reaction_characteristics",
            "chem_energy_changes",
            "chem_combination_decomposition",
            "chem_displacement_reactions",
            "chem_redox_reactions",
            "chem_corrosion_rancidity",
        ],
    },
    {
        "chapter": "Acids, Bases and Salts",
        "chapter_number": 2,
        "concepts": [
            "acids_indicators_properties",
            "acids_metal_carbonate_rxns",
            "acids_neutralisation_ions",
            "acids_ph_scale",
            "acids_chlor_alkali_salts",
        ],
    },
    {
        "chapter": "Metals and Non-metals",
        "chapter_number": 3,
        "concepts": [
            "metals_physical_chemical_props",
            "metals_reactivity_series",
            "metals_ionic_bonding",
            "metals_metallurgy_extraction",
            "metals_corrosion_alloys",
        ],
    },
    {
        "chapter": "Carbon and its Compounds",
        "chapter_number": 4,
        "concepts": [
            "carbon_covalent_bonding",
            "carbon_allotropes_structure",
            "carbon_hydrocarbons_homologous",
            "carbon_functional_groups_isomers",
            "carbon_chemical_reactions",
        ],
    },
    {
        "chapter": "Life Processes",
        "chapter_number": 5,
        "concepts": [
            "bio_nutrition",
            "bio_heterotrophic_digestion",
            "bio_respiration",
            "bio_transport_circulation",
            "bio_excretion",
        ],
    },
    {
        "chapter": "Control and Coordination",
        "chapter_number": 6,
        "concepts": [
            "coord_nervous_system",
            "coord_reflex_arc",
            "coord_brain_structure",
            "coord_hormones_endocrine",
            "coord_plant_hormones",
        ],
    },
    {
        "chapter": "How do Organisms Reproduce?",
        "chapter_number": 7,
        "concepts": [
            "repro_asexual_modes",
            "repro_sexual_reproduction",
            "repro_human_reproductive_system",
            "repro_menstrual_cycle",
            "repro_contraception",
        ],
    },
    {
        "chapter": "Heredity",
        "chapter_number": 8,
        "concepts": [
            "heredity_mendel_laws",
            "heredity_monohybrid_cross",
            "heredity_dihybrid_cross",
            "heredity_sex_determination",
            "heredity_evolution_basics",
        ],
    },
    {
        "chapter": "Light – Reflection and Refraction",
        "chapter_number": 9,
        "concepts": [
            "light_reflection_laws",
            "light_spherical_mirrors",
            "light_mirror_formula",
            "light_refraction_laws",
            "light_lens_formula",
        ],
    },
    {
        "chapter": "The Human Eye and the Colourful World",
        "chapter_number": 10,
        "concepts": [
            "eye_structure_function",
            "eye_defects_correction",
            "eye_prism_dispersion",
            "eye_scattering_tyndall",
        ],
    },
    {
        "chapter": "Electricity",
        "chapter_number": 11,
        "concepts": [
            "elec_current_potential",
            "elec_ohms_law",
            "elec_resistance_resistivity",
            "elec_series_parallel",
            "elec_heating_power",
        ],
    },
    {
        "chapter": "Magnetic Effects of Electric Current",
        "chapter_number": 12,
        "concepts": [
            "mag_field_lines",
            "mag_solenoid_electromagnet",
            "mag_force_conductor",
            "mag_electromagnetic_induction",
            "mag_electric_motor_generator",
        ],
    },
    {
        "chapter": "Our Environment",
        "chapter_number": 13,
        "concepts": [
            "env_ecosystem_components",
            "env_food_chains_webs",
            "env_energy_flow",
            "env_ozone_depletion",
            "env_waste_management",
        ],
    },
]

CLASS_10_MATH = [
    {
        "chapter": "Real Numbers",
        "chapter_number": 1,
        "concepts": [
            "real_euclids_division",
            "real_fundamental_theorem",
            "real_irrational_proofs",
            "real_decimal_expansions",
        ],
    },
    {
        "chapter": "Polynomials",
        "chapter_number": 2,
        "concepts": [
            "poly_zeroes_graphs",
            "poly_relationship_coefficients",
            "poly_division_algorithm",
        ],
    },
    {
        "chapter": "Pair of Linear Equations in Two Variables",
        "chapter_number": 3,
        "concepts": [
            "linear_graphical_method",
            "linear_algebraic_methods",
            "linear_cross_multiplication",
            "linear_consistency",
        ],
    },
    {
        "chapter": "Quadratic Equations",
        "chapter_number": 4,
        "concepts": [
            "quad_standard_form",
            "quad_factorisation",
            "quad_completing_square",
            "quad_discriminant_nature",
        ],
    },
    {
        "chapter": "Arithmetic Progressions",
        "chapter_number": 5,
        "concepts": ["ap_nth_term", "ap_sum_n_terms", "ap_common_difference", "ap_applications"],
    },
    {
        "chapter": "Triangles",
        "chapter_number": 6,
        "concepts": [
            "tri_similarity_criteria",
            "tri_basic_proportionality",
            "tri_pythagoras_theorem",
            "tri_areas_similar",
        ],
    },
    {
        "chapter": "Coordinate Geometry",
        "chapter_number": 7,
        "concepts": ["coord_distance_formula", "coord_section_formula", "coord_area_triangle"],
    },
    {
        "chapter": "Introduction to Trigonometry",
        "chapter_number": 8,
        "concepts": [
            "trig_ratios",
            "trig_specific_angles",
            "trig_complementary_angles",
            "trig_identities",
        ],
    },
    {
        "chapter": "Some Applications of Trigonometry",
        "chapter_number": 9,
        "concepts": [
            "trig_app_heights_distances",
            "trig_app_angle_elevation",
            "trig_app_angle_depression",
        ],
    },
    {
        "chapter": "Circles",
        "chapter_number": 10,
        "concepts": ["circle_tangent_properties", "circle_tangent_theorems"],
    },
    {
        "chapter": "Areas Related to Circles",
        "chapter_number": 11,
        "concepts": ["circle_area_sector", "circle_area_segment", "circle_combined_figures"],
    },
    {
        "chapter": "Surface Areas and Volumes",
        "chapter_number": 12,
        "concepts": ["sav_combination_solids", "sav_conversion_shapes", "sav_frustum_cone"],
    },
    {
        "chapter": "Statistics",
        "chapter_number": 13,
        "concepts": [
            "stats_mean_methods",
            "stats_median_grouped",
            "stats_mode_grouped",
            "stats_ogive_cumulative",
        ],
    },
    {
        "chapter": "Probability",
        "chapter_number": 14,
        "concepts": ["prob_theoretical", "prob_complementary_events", "prob_impossible_sure"],
    },
]


# ---------------------------------------------------------------------------
# REALISTIC NCERT QUESTION BANKS — Real NCERT-style MCQs
# ---------------------------------------------------------------------------


def _make_question_bank():
    """Returns a dict: chapter_name -> list of question dicts."""
    bank = {}

    # ===================== CLASS 10 SCIENCE =====================
    bank["Chemical Reactions and Equations"] = [
        {
            "q": "Which of the following is an example of a double displacement reaction?",
            "options": [
                "A) NaOH + HCl → NaCl + H₂O",
                "B) 2Mg + O₂ → 2MgO",
                "C) Zn + CuSO₄ → ZnSO₄ + Cu",
                "D) 2H₂O → 2H₂ + O₂",
            ],
            "correct": "A",
            "explanation": "NaOH + HCl is a neutralization reaction which is a type of double displacement where ions exchange partners.",
            "pages": [6, 7],
        },
        {
            "q": "What happens when a solution of iron (II) sulphate is electrolysed?",
            "options": [
                "A) Iron is deposited at cathode",
                "B) Oxygen is released at cathode",
                "C) Hydrogen is released at anode",
                "D) Sulphur is deposited at anode",
            ],
            "correct": "A",
            "explanation": "During electrolysis of FeSO₄, Fe²⁺ ions migrate to cathode and get deposited as iron metal.",
            "pages": [10, 11],
        },
        {
            "q": "Rancidity can be prevented by:",
            "options": [
                "A) Adding antioxidants",
                "B) Storing in sunlight",
                "C) Adding water",
                "D) Heating the food repeatedly",
            ],
            "correct": "A",
            "explanation": "Antioxidants like BHA and BHT prevent oxidation of fats and oils, thus preventing rancidity.",
            "pages": [14, 15],
        },
        {
            "q": "Which gas is released when zinc reacts with dilute hydrochloric acid?",
            "options": ["A) Oxygen", "B) Chlorine", "C) Hydrogen", "D) Nitrogen"],
            "correct": "C",
            "explanation": "Zn + 2HCl → ZnCl₂ + H₂↑. Hydrogen gas is released with effervescence.",
            "pages": [4, 5],
        },
        {
            "q": "The process of reduction involves:",
            "options": [
                "A) Gain of oxygen",
                "B) Loss of electrons",
                "C) Gain of hydrogen",
                "D) Loss of hydrogen",
            ],
            "correct": "C",
            "explanation": "Reduction is defined as gain of hydrogen or loss of oxygen, or gain of electrons.",
            "pages": [12, 13],
        },
        {
            "q": "Which of the following is an endothermic reaction?",
            "options": [
                "A) Burning of natural gas",
                "B) Decomposition of vegetable matter",
                "C) Decomposition of calcium carbonate on heating",
                "D) Respiration",
            ],
            "correct": "C",
            "explanation": "CaCO₃ → CaO + CO₂ requires continuous supply of heat, making it endothermic.",
            "pages": [8, 9],
        },
        {
            "q": "Balancing a chemical equation is based on:",
            "options": [
                "A) Law of conservation of energy",
                "B) Law of conservation of mass",
                "C) Law of definite proportions",
                "D) Avogadro's law",
            ],
            "correct": "B",
            "explanation": "A balanced equation follows the law of conservation of mass — atoms are neither created nor destroyed.",
            "pages": [2, 3],
        },
        {
            "q": "When copper powder is heated in air, it forms:",
            "options": ["A) CuO (black)", "B) Cu₂O (red)", "C) CuSO₄ (blue)", "D) CuCl₂ (green)"],
            "correct": "A",
            "explanation": "2Cu + O₂ → 2CuO. Copper reacts with oxygen to form black copper oxide.",
            "pages": [6, 7],
        },
        {
            "q": "Which type of chemical reaction takes place when electricity is passed through water?",
            "options": [
                "A) Displacement",
                "B) Combination",
                "C) Decomposition",
                "D) Double displacement",
            ],
            "correct": "C",
            "explanation": "Electrolysis of water (2H₂O → 2H₂ + O₂) is an electrolytic decomposition reaction.",
            "pages": [9, 10],
        },
        {
            "q": "Iron articles rust faster in:",
            "options": ["A) Dry air", "B) Distilled water", "C) Salty water", "D) Boiled water"],
            "correct": "C",
            "explanation": "Salt water accelerates rusting by acting as an electrolyte, facilitating the electrochemical process of corrosion.",
            "pages": [14, 15],
        },
    ]

    bank["Acids, Bases and Salts"] = [
        {
            "q": "What is the pH of a neutral solution?",
            "options": ["A) 0", "B) 7", "C) 14", "D) 1"],
            "correct": "B",
            "explanation": "A neutral solution has pH = 7. Below 7 is acidic, above 7 is basic.",
            "pages": [18, 19],
        },
        {
            "q": "Which indicator turns pink in a basic solution?",
            "options": ["A) Methyl orange", "B) Litmus", "C) Phenolphthalein", "D) Turmeric"],
            "correct": "C",
            "explanation": "Phenolphthalein is colourless in acidic/neutral solutions and turns pink in basic solutions.",
            "pages": [16, 17],
        },
        {
            "q": "When an acid reacts with a metal, the gas evolved is:",
            "options": ["A) CO₂", "B) O₂", "C) H₂", "D) N₂"],
            "correct": "C",
            "explanation": "Metal + Acid → Salt + Hydrogen gas. The pop sound confirms hydrogen evolution.",
            "pages": [20, 21],
        },
        {
            "q": "Plaster of Paris is chemically:",
            "options": ["A) CaSO₄·2H₂O", "B) CaSO₄·½H₂O", "C) CaSO₄", "D) Ca(OH)₂"],
            "correct": "B",
            "explanation": "Plaster of Paris is calcium sulphate hemihydrate (CaSO₄·½H₂O), obtained by heating gypsum.",
            "pages": [28, 29],
        },
        {
            "q": "The chemical formula of baking soda is:",
            "options": ["A) Na₂CO₃", "B) NaHCO₃", "C) NaOH", "D) NaCl"],
            "correct": "B",
            "explanation": "Baking soda is sodium hydrogen carbonate (NaHCO₃), used in cooking and fire extinguishers.",
            "pages": [26, 27],
        },
        {
            "q": "Tooth decay starts when pH of the mouth is:",
            "options": [
                "A) Greater than 7",
                "B) Less than 5.5",
                "C) Equal to 7",
                "D) Greater than 9.2",
            ],
            "correct": "B",
            "explanation": "When pH in the mouth falls below 5.5, tooth enamel (calcium phosphate) starts corroding.",
            "pages": [22, 23],
        },
        {
            "q": "Which of these is a strong acid?",
            "options": [
                "A) Acetic acid",
                "B) Citric acid",
                "C) Hydrochloric acid",
                "D) Carbonic acid",
            ],
            "correct": "C",
            "explanation": "HCl completely dissociates in water, producing a large number of H⁺ ions — it's a strong acid.",
            "pages": [18, 19],
        },
        {
            "q": "The reaction between an acid and a base is called:",
            "options": ["A) Decomposition", "B) Oxidation", "C) Neutralisation", "D) Displacement"],
            "correct": "C",
            "explanation": "Acid + Base → Salt + Water. This exothermic reaction is called neutralisation.",
            "pages": [22, 23],
        },
        {
            "q": "Common salt (NaCl) is obtained by evaporation of:",
            "options": ["A) River water", "B) Sea water", "C) Distilled water", "D) Mineral water"],
            "correct": "B",
            "explanation": "Common salt is obtained by the solar evaporation of sea water in coastal areas.",
            "pages": [24, 25],
        },
        {
            "q": "Bleaching powder has the chemical formula:",
            "options": ["A) Ca(OCl)Cl", "B) CaCl₂", "C) Ca(OH)₂", "D) CaO"],
            "correct": "A",
            "explanation": "Bleaching powder is calcium oxychloride Ca(OCl)Cl, made by the action of chlorine on slaked lime.",
            "pages": [26, 27],
        },
    ]

    bank["Metals and Non-metals"] = [
        {
            "q": "Which of the following metals is the most reactive?",
            "options": ["A) Copper", "B) Iron", "C) Potassium", "D) Gold"],
            "correct": "C",
            "explanation": "In the reactivity series, potassium is the most reactive metal, reacting violently even with cold water.",
            "pages": [32, 33],
        },
        {
            "q": "An alloy of copper and zinc is called:",
            "options": ["A) Bronze", "B) Brass", "C) Solder", "D) Steel"],
            "correct": "B",
            "explanation": "Brass is an alloy of copper (Cu) and zinc (Zn), commonly used in utensils and decorative items.",
            "pages": [46, 47],
        },
        {
            "q": "Ionic compounds have:",
            "options": [
                "A) Low melting points",
                "B) High melting points",
                "C) No electrical conductivity",
                "D) Covalent bonds",
            ],
            "correct": "B",
            "explanation": "Ionic compounds have strong electrostatic forces between ions, requiring high energy to break — hence high melting points.",
            "pages": [38, 39],
        },
        {
            "q": "Which metal is stored in kerosene?",
            "options": ["A) Copper", "B) Sodium", "C) Iron", "D) Aluminium"],
            "correct": "B",
            "explanation": "Sodium is extremely reactive and catches fire in open air, so it is stored under kerosene to prevent contact with air and moisture.",
            "pages": [34, 35],
        },
        {
            "q": "The process of obtaining a metal from its ore is called:",
            "options": ["A) Mining", "B) Metallurgy", "C) Galvanisation", "D) Alloying"],
            "correct": "B",
            "explanation": "Metallurgy includes all the steps from ore extraction to purification of the metal.",
            "pages": [40, 41],
        },
        {
            "q": "Which non-metal is essential for our life and all living beings inhale during breathing?",
            "options": ["A) Nitrogen", "B) Hydrogen", "C) Oxygen", "D) Chlorine"],
            "correct": "C",
            "explanation": "Oxygen is essential for respiration — the process by which living organisms release energy from food.",
            "pages": [30, 31],
        },
        {
            "q": "Galvanisation is a method of protecting iron from rusting by coating it with:",
            "options": ["A) Copper", "B) Tin", "C) Zinc", "D) Chromium"],
            "correct": "C",
            "explanation": "In galvanisation, a thin layer of zinc is deposited on iron to protect it from corrosion.",
            "pages": [46, 47],
        },
        {
            "q": "Which metal can be cut with a knife?",
            "options": ["A) Iron", "B) Copper", "C) Sodium", "D) Gold"],
            "correct": "C",
            "explanation": "Sodium and potassium are so soft that they can be easily cut with a knife.",
            "pages": [30, 31],
        },
        {
            "q": "Anodising is done on:",
            "options": ["A) Iron", "B) Aluminium", "C) Copper", "D) Zinc"],
            "correct": "B",
            "explanation": "Anodising builds a thick, protective oxide layer on aluminium through electrolysis.",
            "pages": [46, 47],
        },
        {
            "q": "Amphoteric oxides react with:",
            "options": ["A) Only acids", "B) Only bases", "C) Both acids and bases", "D) Neither"],
            "correct": "C",
            "explanation": "Amphoteric oxides like Al₂O₃ and ZnO can react with both acids and bases to form salts and water.",
            "pages": [36, 37],
        },
    ]

    bank["Carbon and its Compounds"] = [
        {
            "q": "The covalent bond in a molecule of hydrogen is formed by:",
            "options": [
                "A) Transfer of electrons",
                "B) Sharing of electrons",
                "C) Donation of electrons",
                "D) Absorption of electrons",
            ],
            "correct": "B",
            "explanation": "In H₂, each hydrogen atom shares one electron to achieve a stable noble gas configuration.",
            "pages": [48, 49],
        },
        {
            "q": "Which of the following is not an allotrope of carbon?",
            "options": ["A) Diamond", "B) Graphite", "C) Silicon", "D) Fullerene"],
            "correct": "C",
            "explanation": "Silicon is a separate element. Diamond, graphite, and fullerene are allotropes of carbon.",
            "pages": [50, 51],
        },
        {
            "q": "Ethanol can be converted to ethanoic acid by:",
            "options": ["A) Reduction", "B) Oxidation", "C) Hydrogenation", "D) Dehydration"],
            "correct": "B",
            "explanation": "Ethanol undergoes oxidation with alkaline KMnO₄ or acidified K₂Cr₂O₇ to form ethanoic acid.",
            "pages": [58, 59],
        },
        {
            "q": "The IUPAC name of CH₃COOH is:",
            "options": [
                "A) Methanoic acid",
                "B) Ethanoic acid",
                "C) Propanoic acid",
                "D) Butanoic acid",
            ],
            "correct": "B",
            "explanation": "CH₃COOH contains 2 carbon atoms. According to IUPAC, it is named ethanoic acid (common name: acetic acid).",
            "pages": [56, 57],
        },
        {
            "q": "Soaps are formed by the reaction of:",
            "options": [
                "A) Acid with alcohol",
                "B) Fat/Oil with NaOH",
                "C) Fat/Oil with HCl",
                "D) Alcohol with NaOH",
            ],
            "correct": "B",
            "explanation": "Saponification is the reaction of fat/oil with sodium hydroxide (NaOH) to produce soap and glycerol.",
            "pages": [62, 63],
        },
        {
            "q": "How many covalent bonds can carbon form?",
            "options": ["A) 2", "B) 3", "C) 4", "D) 5"],
            "correct": "C",
            "explanation": "Carbon has 4 valence electrons and needs 4 more to complete its octet, so it forms 4 covalent bonds.",
            "pages": [48, 49],
        },
        {
            "q": "The first member of the alkene series is:",
            "options": ["A) Methane", "B) Ethene", "C) Ethyne", "D) Propene"],
            "correct": "B",
            "explanation": "Ethene (C₂H₄) is the first member of the alkene homologous series with a C=C double bond.",
            "pages": [52, 53],
        },
        {
            "q": "Acetic acid when dissolved in water gives:",
            "options": ["A) Strong acid", "B) Weak acid", "C) Strong base", "D) Neutral solution"],
            "correct": "B",
            "explanation": "Acetic acid is a weak acid — it does not completely dissociate in water.",
            "pages": [58, 59],
        },
        {
            "q": "Versatile nature of carbon is due to:",
            "options": [
                "A) Its tetravalency and catenation",
                "B) Its atomic mass",
                "C) Its large atomic size",
                "D) Its electronegativity only",
            ],
            "correct": "A",
            "explanation": "Carbon's ability to form 4 bonds (tetravalency) and long chains (catenation) makes it versatile.",
            "pages": [48, 49],
        },
        {
            "q": "Detergents are preferred over soaps because:",
            "options": [
                "A) They are cheaper",
                "B) They work in hard water",
                "C) They are biodegradable",
                "D) They have pleasant smell",
            ],
            "correct": "B",
            "explanation": "Detergents do not form insoluble precipitates with Ca²⁺ and Mg²⁺ ions in hard water, unlike soaps.",
            "pages": [62, 63],
        },
    ]

    bank["Life Processes"] = [
        {
            "q": "The main site of photosynthesis in a leaf is:",
            "options": [
                "A) Epidermis",
                "B) Guard cells",
                "C) Mesophyll cells",
                "D) Vascular bundle",
            ],
            "correct": "C",
            "explanation": "Mesophyll cells contain abundant chloroplasts where most photosynthesis occurs.",
            "pages": [66, 67],
        },
        {
            "q": "Which blood vessels carry blood from the heart to the lungs?",
            "options": ["A) Pulmonary veins", "B) Aorta", "C) Pulmonary arteries", "D) Vena cava"],
            "correct": "C",
            "explanation": "Pulmonary arteries carry deoxygenated blood from the right ventricle to the lungs for oxygenation.",
            "pages": [76, 77],
        },
        {
            "q": "The role of HCl in the stomach is to:",
            "options": [
                "A) Digest fats",
                "B) Activate pepsinogen to pepsin",
                "C) Emulsify fats",
                "D) Absorb nutrients",
            ],
            "correct": "B",
            "explanation": "HCl creates an acidic medium (pH ~2) that activates pepsinogen into pepsin for protein digestion.",
            "pages": [70, 71],
        },
        {
            "q": "In human beings, the correct sequence of air passage is:",
            "options": [
                "A) Nostrils → Pharynx → Larynx → Trachea → Bronchi → Alveoli",
                "B) Nostrils → Larynx → Pharynx → Bronchi → Trachea → Alveoli",
                "C) Nostrils → Pharynx → Trachea → Larynx → Bronchi → Alveoli",
                "D) Nostrils → Trachea → Pharynx → Larynx → Bronchi → Alveoli",
            ],
            "correct": "A",
            "explanation": "Air enters nostrils → pharynx → larynx → trachea → bronchi → bronchioles → alveoli.",
            "pages": [72, 73],
        },
        {
            "q": "The excretory unit of the kidney is called:",
            "options": ["A) Neuron", "B) Nephron", "C) Glomerulus", "D) Bowman's capsule"],
            "correct": "B",
            "explanation": "Each kidney contains about 1 million nephrons that filter blood and produce urine.",
            "pages": [80, 81],
        },
        {
            "q": "Which of the following is NOT a function of the large intestine?",
            "options": [
                "A) Absorption of water",
                "B) Digestion of cellulose",
                "C) Absorption of some minerals",
                "D) Storage of undigested food",
            ],
            "correct": "B",
            "explanation": "Humans lack cellulase enzyme, so cellulose (fibre) is not digested in the large intestine.",
            "pages": [70, 71],
        },
        {
            "q": "Double circulation means:",
            "options": [
                "A) Blood passes through the heart once",
                "B) Blood passes through the heart twice in one complete cycle",
                "C) Heart beats twice per cycle",
                "D) Blood flows in two arteries",
            ],
            "correct": "B",
            "explanation": "In double circulation, blood passes through the heart twice — once for pulmonary and once for systemic circulation.",
            "pages": [76, 77],
        },
        {
            "q": "The opening and closing of stomata is controlled by:",
            "options": [
                "A) Epidermal cells",
                "B) Guard cells",
                "C) Palisade cells",
                "D) Companion cells",
            ],
            "correct": "B",
            "explanation": "Guard cells regulate stomatal opening by changing their turgidity through water uptake or loss.",
            "pages": [68, 69],
        },
        {
            "q": "Anaerobic respiration in yeast produces:",
            "options": [
                "A) CO₂ and water",
                "B) Ethanol and CO₂",
                "C) Lactic acid",
                "D) Pyruvic acid only",
            ],
            "correct": "B",
            "explanation": "In yeast, anaerobic respiration (fermentation) produces ethanol and CO₂ from glucose.",
            "pages": [74, 75],
        },
        {
            "q": "Which of the following is the correct equation for photosynthesis?",
            "options": [
                "A) 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂",
                "B) C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O",
                "C) 6CO₂ + 12H₂O → C₆H₁₂O₆ + 6O₂ + 6H₂O",
                "D) CO₂ + H₂O → CH₂O + O₂",
            ],
            "correct": "C",
            "explanation": "The balanced equation for photosynthesis is 6CO₂ + 12H₂O → C₆H₁₂O₆ + 6O₂ + 6H₂O.",
            "pages": [66, 67],
        },
    ]

    bank["Control and Coordination"] = [
        {
            "q": "The gap between two neurons is called:",
            "options": ["A) Dendrite", "B) Synapse", "C) Axon", "D) Impulse"],
            "correct": "B",
            "explanation": "A synapse is the tiny gap between the terminal of one neuron and the dendrite of the next.",
            "pages": [84, 85],
        },
        {
            "q": "Which part of the brain controls involuntary actions like blood pressure and vomiting?",
            "options": ["A) Cerebrum", "B) Cerebellum", "C) Medulla oblongata", "D) Pons"],
            "correct": "C",
            "explanation": "Medulla oblongata (hindbrain) controls involuntary functions like breathing, heart rate, and blood pressure.",
            "pages": [86, 87],
        },
        {
            "q": "Adrenaline is secreted by:",
            "options": [
                "A) Thyroid gland",
                "B) Pituitary gland",
                "C) Adrenal glands",
                "D) Pancreas",
            ],
            "correct": "C",
            "explanation": "Adrenaline (emergency hormone) is secreted by the adrenal glands situated on top of kidneys.",
            "pages": [90, 91],
        },
        {
            "q": "Which plant hormone promotes growth?",
            "options": ["A) Abscisic acid", "B) Auxin", "C) Ethylene", "D) Cytokinin"],
            "correct": "B",
            "explanation": "Auxin promotes cell elongation and growth, especially at the shoot tips.",
            "pages": [82, 83],
        },
        {
            "q": "Iodine deficiency causes:",
            "options": ["A) Diabetes", "B) Goitre", "C) Dwarfism", "D) Rickets"],
            "correct": "B",
            "explanation": "Iodine is essential for thyroxine production. Its deficiency causes enlargement of the thyroid gland — goitre.",
            "pages": [90, 91],
        },
        {
            "q": "A reflex arc involves:",
            "options": [
                "A) Brain only",
                "B) Spinal cord only",
                "C) Receptor → Sensory neuron → Spinal cord → Motor neuron → Effector",
                "D) Receptor → Motor neuron → Brain → Sensory neuron → Effector",
            ],
            "correct": "C",
            "explanation": "A reflex arc is the shortest neural pathway: receptor → sensory neuron → spinal cord → motor neuron → effector.",
            "pages": [84, 85],
        },
        {
            "q": "Diabetes is caused by deficiency of:",
            "options": ["A) Thyroxine", "B) Growth hormone", "C) Insulin", "D) Adrenaline"],
            "correct": "C",
            "explanation": "Insulin (from pancreas) regulates blood sugar. Its deficiency leads to diabetes mellitus.",
            "pages": [90, 91],
        },
        {
            "q": "Phototropism in plants is caused by:",
            "options": [
                "A) Equal distribution of auxin",
                "B) Unequal distribution of auxin",
                "C) Gibberellin",
                "D) Abscisic acid",
            ],
            "correct": "B",
            "explanation": "Unequal distribution of auxin causes the shaded side to grow more, bending the plant toward light.",
            "pages": [82, 83],
        },
        {
            "q": "Which hormone is responsible for the development of male secondary sexual characters?",
            "options": ["A) Oestrogen", "B) Progesterone", "C) Testosterone", "D) Insulin"],
            "correct": "C",
            "explanation": "Testosterone is produced by testes and is responsible for male secondary sexual characters like facial hair and deeper voice.",
            "pages": [92, 93],
        },
        {
            "q": "The cerebellum controls:",
            "options": [
                "A) Thinking and memory",
                "B) Balance and posture",
                "C) Breathing",
                "D) Hunger and thirst",
            ],
            "correct": "B",
            "explanation": "The cerebellum coordinates voluntary muscle movements, maintains balance and posture.",
            "pages": [86, 87],
        },
    ]

    bank["How do Organisms Reproduce?"] = [
        {
            "q": "Binary fission in Amoeba is a type of:",
            "options": [
                "A) Sexual reproduction",
                "B) Asexual reproduction",
                "C) Vegetative propagation",
                "D) Budding",
            ],
            "correct": "B",
            "explanation": "Binary fission is an asexual reproduction method where Amoeba divides into two daughter cells.",
            "pages": [94, 95],
        },
        {
            "q": "The male reproductive part of a flower is:",
            "options": ["A) Pistil", "B) Stamen", "C) Ovary", "D) Stigma"],
            "correct": "B",
            "explanation": "Stamen (consisting of anther and filament) is the male reproductive organ producing pollen grains.",
            "pages": [100, 101],
        },
        {
            "q": "In human males, sperm are produced in:",
            "options": ["A) Prostate gland", "B) Seminal vesicles", "C) Testes", "D) Vas deferens"],
            "correct": "C",
            "explanation": "Testes produce sperms and the male hormone testosterone.",
            "pages": [102, 103],
        },
        {
            "q": "Copper-T is a type of:",
            "options": [
                "A) Surgical method",
                "B) Barrier method",
                "C) Chemical method",
                "D) Intrauterine device",
            ],
            "correct": "D",
            "explanation": "Copper-T is an IUD placed inside the uterus to prevent pregnancy.",
            "pages": [106, 107],
        },
        {
            "q": "The correct sequence of stages during menstrual cycle is:",
            "options": [
                "A) Menstruation → Ovulation → Fertilisation → Implantation",
                "B) Ovulation → Menstruation → Fertilisation → Implantation",
                "C) Fertilisation → Menstruation → Ovulation → Implantation",
                "D) Implantation → Menstruation → Ovulation → Fertilisation",
            ],
            "correct": "A",
            "explanation": "The menstrual cycle progresses from menstruation to follicular phase to ovulation, and if fertilisation occurs, implantation follows.",
            "pages": [104, 105],
        },
        {
            "q": "Regeneration is carried out by:",
            "options": ["A) Hydra", "B) Planaria", "C) Amoeba", "D) Both A and B"],
            "correct": "D",
            "explanation": "Both Hydra and Planaria can regenerate — they grow new organisms from cut body parts using specialised cells.",
            "pages": [94, 95],
        },
        {
            "q": "The function of ovary in a flower is to produce:",
            "options": ["A) Pollen grains", "B) Nectar", "C) Ovules", "D) Petals"],
            "correct": "C",
            "explanation": "The ovary contains ovules which, after fertilisation, develop into seeds.",
            "pages": [100, 101],
        },
        {
            "q": "Which is an example of vegetative propagation?",
            "options": [
                "A) Seeds of mustard",
                "B) Eyes of potato",
                "C) Spores of fern",
                "D) Eggs of frog",
            ],
            "correct": "B",
            "explanation": "The 'eyes' (buds) on a potato tuber can grow into new plants — this is vegetative propagation.",
            "pages": [96, 97],
        },
        {
            "q": "DNA copies are generated during reproduction for:",
            "options": [
                "A) Maintaining exact genetic information",
                "B) Creating variations",
                "C) Both A and B",
                "D) Neither A nor B",
            ],
            "correct": "C",
            "explanation": "DNA copying during reproduction maintains genetic information while small variations accumulate due to imperfect copying.",
            "pages": [94, 95],
        },
        {
            "q": "Fertilisation in humans occurs in the:",
            "options": ["A) Uterus", "B) Ovary", "C) Fallopian tube (oviduct)", "D) Vagina"],
            "correct": "C",
            "explanation": "Fertilisation normally occurs in the fallopian tube (oviduct) when sperm meets the ovum.",
            "pages": [104, 105],
        },
    ]

    bank["Heredity"] = [
        {
            "q": "If a pure tall plant (TT) is crossed with a pure short plant (tt), the F₁ generation will be:",
            "options": [
                "A) All tall",
                "B) All short",
                "C) 50% tall, 50% short",
                "D) 75% tall, 25% short",
            ],
            "correct": "A",
            "explanation": "In a monohybrid cross, F₁ generation shows only the dominant trait (tall). All plants are Tt (heterozygous tall).",
            "pages": [108, 109],
        },
        {
            "q": "In humans, the sex of a child is determined by:",
            "options": [
                "A) The mother's chromosomes",
                "B) The father's chromosomes",
                "C) Environmental factors",
                "D) Blood type of parents",
            ],
            "correct": "B",
            "explanation": "The father contributes either X or Y chromosome. XX results in a girl, XY results in a boy.",
            "pages": [114, 115],
        },
        {
            "q": "The ratio of phenotypes in F₂ generation of a monohybrid cross is:",
            "options": ["A) 1:1", "B) 1:2:1", "C) 3:1", "D) 9:3:3:1"],
            "correct": "C",
            "explanation": "Mendel's monohybrid F₂ ratio is 3 dominant : 1 recessive (phenotypic ratio).",
            "pages": [110, 111],
        },
        {
            "q": "Mendel used which plant for his experiments?",
            "options": ["A) Rose", "B) Mango", "C) Garden pea", "D) Sunflower"],
            "correct": "C",
            "explanation": "Mendel chose garden pea (Pisum sativum) because of its distinct contrasting traits, short life cycle, and easy cross-pollination.",
            "pages": [108, 109],
        },
        {
            "q": "A trait carried on the X chromosome is called:",
            "options": [
                "A) Autosomal trait",
                "B) Sex-linked trait",
                "C) Dominant trait",
                "D) Recessive trait",
            ],
            "correct": "B",
            "explanation": "Traits linked to genes on sex chromosomes (especially X) are called sex-linked traits, e.g., colour blindness.",
            "pages": [114, 115],
        },
        {
            "q": "An organism's observable characteristics are called its:",
            "options": ["A) Genotype", "B) Phenotype", "C) Chromosome", "D) Allele"],
            "correct": "B",
            "explanation": "Phenotype refers to the physical appearance — the observable characteristics of an organism.",
            "pages": [110, 111],
        },
        {
            "q": "The number of chromosomes in human body cells is:",
            "options": ["A) 23", "B) 44", "C) 46", "D) 48"],
            "correct": "C",
            "explanation": "Human somatic (body) cells contain 46 chromosomes (23 pairs) — 22 autosomal pairs + 1 pair of sex chromosomes.",
            "pages": [112, 113],
        },
        {
            "q": "Genes are located on:",
            "options": ["A) Chromosomes", "B) Ribosomes", "C) Lysosomes", "D) Cell membrane"],
            "correct": "A",
            "explanation": "Genes are segments of DNA located on chromosomes that carry hereditary information.",
            "pages": [112, 113],
        },
        {
            "q": "Evolution cannot be equated with:",
            "options": [
                "A) Change in gene frequency",
                "B) Progress from lower to higher",
                "C) Adaptation to environment",
                "D) Natural selection",
            ],
            "correct": "B",
            "explanation": "Evolution is not 'progress' — it is adaptation to different environments. Simpler organisms are not 'lower'.",
            "pages": [116, 117],
        },
        {
            "q": "Variations are useful for the survival of species because:",
            "options": [
                "A) They make organisms beautiful",
                "B) They enable better adaptation to changing environment",
                "C) They increase body size",
                "D) They reduce competition",
            ],
            "correct": "B",
            "explanation": "Variations ensure that at least some individuals survive drastic environmental changes, benefiting species survival.",
            "pages": [108, 109],
        },
    ]

    bank["Light – Reflection and Refraction"] = [
        {
            "q": "The image formed by a plane mirror is:",
            "options": [
                "A) Real and inverted",
                "B) Virtual, erect and laterally inverted",
                "C) Real and magnified",
                "D) Virtual and diminished",
            ],
            "correct": "B",
            "explanation": "A plane mirror always forms a virtual, erect, same-size, and laterally inverted image.",
            "pages": [118, 119],
        },
        {
            "q": "The focal length of a concave mirror is 15 cm. Its radius of curvature is:",
            "options": ["A) 15 cm", "B) 7.5 cm", "C) 30 cm", "D) 45 cm"],
            "correct": "C",
            "explanation": "R = 2f. If f = 15 cm, then R = 2 × 15 = 30 cm.",
            "pages": [120, 121],
        },
        {
            "q": "A ray of light travelling from a denser to a rarer medium:",
            "options": [
                "A) Bends toward normal",
                "B) Bends away from normal",
                "C) Goes undeviated",
                "D) Gets absorbed",
            ],
            "correct": "B",
            "explanation": "When light goes from denser to rarer medium, it bends away from the normal (speed increases).",
            "pages": [126, 127],
        },
        {
            "q": "The SI unit of power of a lens is:",
            "options": ["A) Metre", "B) Centimetre", "C) Dioptre", "D) Watt"],
            "correct": "C",
            "explanation": "Power of a lens P = 1/f (in metres). The SI unit is dioptre (D).",
            "pages": [130, 131],
        },
        {
            "q": "For a convex lens, when the object is placed at 2F₁, the image formed is:",
            "options": [
                "A) At F₂, real, inverted, diminished",
                "B) At 2F₂, real, inverted, same size",
                "C) Beyond 2F₂, real, inverted, magnified",
                "D) At infinity",
            ],
            "correct": "B",
            "explanation": "When the object is at 2F₁ of a convex lens, the image is at 2F₂ — real, inverted, and same size.",
            "pages": [128, 129],
        },
        {
            "q": "The mirror formula is:",
            "options": [
                "A) 1/f = 1/v + 1/u",
                "B) 1/f = 1/v − 1/u",
                "C) f = u + v",
                "D) f = uv/(u+v)",
            ],
            "correct": "A",
            "explanation": "The mirror formula is 1/f = 1/v + 1/u, where f is focal length, v is image distance, u is object distance.",
            "pages": [122, 123],
        },
        {
            "q": "Refractive index of glass with respect to air is 1.5. The speed of light in glass is:",
            "options": ["A) 3 × 10⁸ m/s", "B) 2 × 10⁸ m/s", "C) 4.5 × 10⁸ m/s", "D) 1.5 × 10⁸ m/s"],
            "correct": "B",
            "explanation": "n = c/v, so v = c/n = 3×10⁸/1.5 = 2×10⁸ m/s.",
            "pages": [126, 127],
        },
        {
            "q": "Which mirror is used as a rear-view mirror in vehicles?",
            "options": [
                "A) Concave mirror",
                "B) Convex mirror",
                "C) Plane mirror",
                "D) Cylindrical mirror",
            ],
            "correct": "B",
            "explanation": "Convex mirrors provide a wider field of view and always form erect, diminished virtual images — ideal for rear-view mirrors.",
            "pages": [124, 125],
        },
        {
            "q": "The phenomenon of bending of light at the boundary of two media is called:",
            "options": ["A) Reflection", "B) Diffraction", "C) Refraction", "D) Dispersion"],
            "correct": "C",
            "explanation": "Refraction is the bending of light as it passes from one medium to another due to change in speed.",
            "pages": [126, 127],
        },
        {
            "q": "A concave mirror is used:",
            "options": [
                "A) As a shaving mirror",
                "B) As a rear-view mirror",
                "C) In street lights",
                "D) Both A and C",
            ],
            "correct": "D",
            "explanation": "Concave mirrors are used as shaving mirrors (magnified image when close) and in vehicle headlights/street lights (reflecting parallel beams).",
            "pages": [124, 125],
        },
    ]

    bank["The Human Eye and the Colourful World"] = [
        {
            "q": "The part of the eye that controls the amount of light entering is:",
            "options": ["A) Cornea", "B) Iris", "C) Lens", "D) Retina"],
            "correct": "B",
            "explanation": "The iris adjusts the pupil size to control the amount of light entering the eye.",
            "pages": [132, 133],
        },
        {
            "q": "The near point of a young person with normal vision is:",
            "options": ["A) 10 cm", "B) 15 cm", "C) 25 cm", "D) 50 cm"],
            "correct": "C",
            "explanation": "The near point (least distance of distinct vision) for a normal eye is about 25 cm.",
            "pages": [134, 135],
        },
        {
            "q": "Myopia is corrected using:",
            "options": [
                "A) Convex lens",
                "B) Concave lens",
                "C) Bifocal lens",
                "D) Cylindrical lens",
            ],
            "correct": "B",
            "explanation": "Myopia (short-sightedness) is corrected using a concave lens of appropriate focal length.",
            "pages": [136, 137],
        },
        {
            "q": "The splitting of white light into its constituent colours is called:",
            "options": ["A) Refraction", "B) Reflection", "C) Dispersion", "D) Scattering"],
            "correct": "C",
            "explanation": "Dispersion is the splitting of white light into 7 colours (VIBGYOR) by a glass prism.",
            "pages": [138, 139],
        },
        {
            "q": "The sky appears blue because of:",
            "options": [
                "A) Reflection of light",
                "B) Refraction of light",
                "C) Scattering of light",
                "D) Absorption of light",
            ],
            "correct": "C",
            "explanation": "Blue light (shorter wavelength) is scattered more by atmospheric particles — Rayleigh scattering.",
            "pages": [140, 141],
        },
        {
            "q": "Stars twinkle because of:",
            "options": [
                "A) They are very far",
                "B) Atmospheric refraction",
                "C) They emit pulsating light",
                "D) Atmospheric reflection",
            ],
            "correct": "B",
            "explanation": "Starlight undergoes atmospheric refraction through layers of different densities, causing apparent twinkling.",
            "pages": [140, 141],
        },
        {
            "q": "Presbyopia is corrected using:",
            "options": [
                "A) Concave lens",
                "B) Convex lens",
                "C) Bifocal lens",
                "D) Cylindrical lens",
            ],
            "correct": "C",
            "explanation": "Presbyopia (age-related near+far vision loss) is corrected with bifocal lenses — concave upper, convex lower.",
            "pages": [136, 137],
        },
        {
            "q": "Tyndall effect is observed when light passes through:",
            "options": ["A) True solution", "B) Colloidal solution", "C) Pure water", "D) Vacuum"],
            "correct": "B",
            "explanation": "Tyndall effect — scattering of light by colloidal particles — makes the light beam visible in a colloid.",
            "pages": [140, 141],
        },
        {
            "q": "The angle of deviation depends on:",
            "options": [
                "A) Angle of prism only",
                "B) Angle of incidence and angle of prism",
                "C) Material of prism only",
                "D) All of the above",
            ],
            "correct": "D",
            "explanation": "Angle of deviation depends on the angle of prism, angle of incidence, and the refractive index (material) of the prism.",
            "pages": [138, 139],
        },
        {
            "q": "At sunrise and sunset, the sun appears reddish because:",
            "options": [
                "A) Sun emits red light at these times",
                "B) Red light is least scattered",
                "C) Blue light is absorbed",
                "D) Atmosphere becomes red",
            ],
            "correct": "B",
            "explanation": "At sunrise/sunset, light travels longer atmospheric path; blue light scatters away, leaving red (least scattered) dominant.",
            "pages": [140, 141],
        },
    ]

    bank["Electricity"] = [
        {
            "q": "The SI unit of electric current is:",
            "options": ["A) Volt", "B) Ohm", "C) Ampere", "D) Watt"],
            "correct": "C",
            "explanation": "Electric current is measured in ampere (A), defined as 1 coulomb of charge flowing per second.",
            "pages": [142, 143],
        },
        {
            "q": "According to Ohm's law, V = IR. If the resistance is doubled and current is halved, the voltage:",
            "options": [
                "A) Doubles",
                "B) Remains same",
                "C) Becomes half",
                "D) Becomes four times",
            ],
            "correct": "B",
            "explanation": "V = IR. If R → 2R and I → I/2, then V = (I/2)(2R) = IR = same.",
            "pages": [146, 147],
        },
        {
            "q": "In a series circuit, the total resistance is:",
            "options": [
                "A) Less than the smallest resistance",
                "B) Equal to the sum of all resistances",
                "C) Equal to the product divided by sum",
                "D) Always 1 ohm",
            ],
            "correct": "B",
            "explanation": "In series: R_total = R₁ + R₂ + R₃ + ... The total resistance is the sum of individual resistances.",
            "pages": [148, 149],
        },
        {
            "q": "The commercial unit of electrical energy is:",
            "options": ["A) Joule", "B) Watt", "C) Kilowatt-hour (kWh)", "D) Calorie"],
            "correct": "C",
            "explanation": "1 kWh = 3.6 × 10⁶ J. Electricity bills are charged per unit (1 unit = 1 kWh).",
            "pages": [152, 153],
        },
        {
            "q": "What is the resistance of a conductor if 0.2 A current flows through it when connected to a 10 V battery?",
            "options": ["A) 2 Ω", "B) 50 Ω", "C) 5 Ω", "D) 0.02 Ω"],
            "correct": "B",
            "explanation": "R = V/I = 10/0.2 = 50 Ω.",
            "pages": [146, 147],
        },
        {
            "q": "Electric fuse works on the principle of:",
            "options": [
                "A) Magnetic effect of current",
                "B) Chemical effect of current",
                "C) Heating effect of current",
                "D) Electromagnetic induction",
            ],
            "correct": "C",
            "explanation": "A fuse wire melts and breaks the circuit when excess current flows — this is the heating effect of current (H = I²Rt).",
            "pages": [152, 153],
        },
        {
            "q": "Which of the following is an insulator?",
            "options": ["A) Copper", "B) Aluminium", "C) Rubber", "D) Silver"],
            "correct": "C",
            "explanation": "Rubber has very high resistance and does not allow electric current to flow — it's an insulator.",
            "pages": [144, 145],
        },
        {
            "q": "In a parallel circuit, the voltage across each resistor is:",
            "options": [
                "A) Different",
                "B) Zero",
                "C) Same as the source voltage",
                "D) Half the source voltage",
            ],
            "correct": "C",
            "explanation": "In parallel combination, the potential difference across each resistor equals the source voltage.",
            "pages": [150, 151],
        },
        {
            "q": "The heating element of an electric iron is made of:",
            "options": ["A) Copper", "B) Aluminium", "C) Nichrome", "D) Silver"],
            "correct": "C",
            "explanation": "Nichrome (Ni-Cr alloy) has high resistivity and high melting point — ideal for heating elements.",
            "pages": [152, 153],
        },
        {
            "q": "1 volt is equal to:",
            "options": [
                "A) 1 joule per ampere",
                "B) 1 joule per coulomb",
                "C) 1 ampere per ohm",
                "D) 1 watt per ampere",
            ],
            "correct": "B",
            "explanation": "1 V = 1 J/C. Voltage is the work done per unit charge.",
            "pages": [142, 143],
        },
    ]

    bank["Magnetic Effects of Electric Current"] = [
        {
            "q": "An electric motor converts:",
            "options": [
                "A) Mechanical energy to electrical energy",
                "B) Electrical energy to mechanical energy",
                "C) Chemical energy to electrical energy",
                "D) Heat energy to electrical energy",
            ],
            "correct": "B",
            "explanation": "An electric motor uses the force on a current-carrying conductor in a magnetic field to produce rotation.",
            "pages": [156, 157],
        },
        {
            "q": "The direction of force on a current-carrying conductor in a magnetic field is given by:",
            "options": [
                "A) Right-hand thumb rule",
                "B) Fleming's left-hand rule",
                "C) Fleming's right-hand rule",
                "D) Ampere's rule",
            ],
            "correct": "B",
            "explanation": "Fleming's left-hand rule: forefinger (field), middle finger (current), thumb (force/motion).",
            "pages": [156, 157],
        },
        {
            "q": "An electromagnetic induction is the process of:",
            "options": [
                "A) Charging a conductor",
                "B) Generating current by changing magnetic field",
                "C) Magnetising iron",
                "D) Heating a conductor",
            ],
            "correct": "B",
            "explanation": "When a magnetic field around a conductor changes, an EMF (and hence current) is induced — electromagnetic induction.",
            "pages": [160, 161],
        },
        {
            "q": "A solenoid behaves like a:",
            "options": [
                "A) Permanent magnet",
                "B) Bar magnet",
                "C) Compass needle",
                "D) Capacitor",
            ],
            "correct": "B",
            "explanation": "A current-carrying solenoid produces a magnetic field pattern similar to a bar magnet with distinct N and S poles.",
            "pages": [154, 155],
        },
        {
            "q": "The direction of induced current is given by:",
            "options": [
                "A) Fleming's left-hand rule",
                "B) Fleming's right-hand rule",
                "C) Right-hand thumb rule",
                "D) Lenz's law only",
            ],
            "correct": "B",
            "explanation": "Fleming's right-hand rule gives the direction of induced current in a generator.",
            "pages": [160, 161],
        },
        {
            "q": "In India, the frequency of alternating current (AC) is:",
            "options": ["A) 60 Hz", "B) 50 Hz", "C) 100 Hz", "D) 25 Hz"],
            "correct": "B",
            "explanation": "In India, the standard AC frequency is 50 Hz (50 cycles per second). In the US, it's 60 Hz.",
            "pages": [162, 163],
        },
        {
            "q": "Magnetic field lines:",
            "options": [
                "A) Intersect each other",
                "B) Are always straight",
                "C) Never intersect",
                "D) Always form closed loops outside the magnet",
            ],
            "correct": "C",
            "explanation": "Magnetic field lines never intersect because at any point, the field has a unique direction.",
            "pages": [154, 155],
        },
        {
            "q": "The core of an electromagnet is made of:",
            "options": ["A) Steel", "B) Soft iron", "C) Copper", "D) Brass"],
            "correct": "B",
            "explanation": "Soft iron is used because it is easily magnetised and demagnetised — ideal for temporary magnets.",
            "pages": [154, 155],
        },
        {
            "q": "A generator works on the principle of:",
            "options": [
                "A) Heating effect",
                "B) Chemical effect",
                "C) Electromagnetic induction",
                "D) Photoelectric effect",
            ],
            "correct": "C",
            "explanation": "An electric generator converts mechanical energy to electrical energy using electromagnetic induction.",
            "pages": [160, 161],
        },
        {
            "q": "The function of a commutator in a DC motor is to:",
            "options": [
                "A) Increase speed",
                "B) Reverse the direction of current every half rotation",
                "C) Decrease resistance",
                "D) Increase voltage",
            ],
            "correct": "B",
            "explanation": "The split-ring commutator reverses current direction every half rotation, ensuring continuous rotation of the coil.",
            "pages": [158, 159],
        },
    ]

    bank["Our Environment"] = [
        {
            "q": "Which of the following constitute a food chain?",
            "options": [
                "A) Grass → Wheat → Mango",
                "B) Grass → Goat → Human",
                "C) Goat → Cow → Elephant",
                "D) Grass → Fish → Goat",
            ],
            "correct": "B",
            "explanation": "Grass (producer) → Goat (primary consumer) → Human (secondary consumer) is a valid food chain.",
            "pages": [164, 165],
        },
        {
            "q": "The percentage of energy transferred to the next trophic level is:",
            "options": ["A) 1%", "B) 10%", "C) 20%", "D) 50%"],
            "correct": "B",
            "explanation": "Only about 10% of energy is transferred from one trophic level to the next (10% law by Lindeman).",
            "pages": [166, 167],
        },
        {
            "q": "Ozone layer depletion is mainly caused by:",
            "options": ["A) CO₂", "B) CFCs (Chlorofluorocarbons)", "C) SO₂", "D) Methane"],
            "correct": "B",
            "explanation": "CFCs release chlorine atoms in the stratosphere which catalytically destroy ozone (O₃) molecules.",
            "pages": [170, 171],
        },
        {
            "q": "Biodegradable wastes include:",
            "options": [
                "A) Plastics",
                "B) Glass bottles",
                "C) Vegetable peels",
                "D) Aluminium cans",
            ],
            "correct": "C",
            "explanation": "Vegetable peels are organic and can be broken down by microorganisms — they are biodegradable.",
            "pages": [168, 169],
        },
        {
            "q": "Decomposers include:",
            "options": [
                "A) Fungi and bacteria",
                "B) Plants and animals",
                "C) Only fungi",
                "D) Herbivores",
            ],
            "correct": "A",
            "explanation": "Decomposers (fungi and bacteria) break down dead organic matter, recycling nutrients back to the soil.",
            "pages": [164, 165],
        },
        {
            "q": "The ozone molecule contains:",
            "options": [
                "A) 2 oxygen atoms",
                "B) 3 oxygen atoms",
                "C) 4 oxygen atoms",
                "D) 1 oxygen atom",
            ],
            "correct": "B",
            "explanation": "Ozone (O₃) is a molecule composed of three atoms of oxygen.",
            "pages": [170, 171],
        },
        {
            "q": "Which of the following is a non-biodegradable waste?",
            "options": ["A) Cotton cloth", "B) Paper bags", "C) Polythene bags", "D) Jute bags"],
            "correct": "C",
            "explanation": "Polythene is a synthetic polymer that is not broken down by biological processes — non-biodegradable.",
            "pages": [168, 169],
        },
        {
            "q": "In an ecosystem, the flow of energy is:",
            "options": [
                "A) Bidirectional",
                "B) Unidirectional",
                "C) Multidirectional",
                "D) Cyclic",
            ],
            "correct": "B",
            "explanation": "Energy flows in one direction: Sun → Producers → Consumers → Decomposers. It is not recycled.",
            "pages": [166, 167],
        },
        {
            "q": "Maximum concentration of harmful chemicals is found in:",
            "options": [
                "A) Primary producers",
                "B) Primary consumers",
                "C) Secondary consumers",
                "D) Tertiary consumers (top predators)",
            ],
            "correct": "D",
            "explanation": "Biological magnification causes highest concentration of non-biodegradable chemicals at the top of the food chain.",
            "pages": [166, 167],
        },
        {
            "q": "The full form of UNEP is:",
            "options": [
                "A) United Nations Environment Programme",
                "B) United Nations Education Policy",
                "C) United Nations Ecology Panel",
                "D) Universal Nature and Environment Protection",
            ],
            "correct": "A",
            "explanation": "UNEP (United Nations Environment Programme) works on environmental issues worldwide.",
            "pages": [170, 171],
        },
    ]

    # ===================== CLASS 9 SCIENCE =====================
    bank["Exploration: Entering the World of Secondary Science"] = [
        {
            "q": "Science is best defined as:",
            "options": [
                "A) A collection of facts",
                "B) A systematic study of nature through observation and experimentation",
                "C) Study of living organisms only",
                "D) Technology development",
            ],
            "correct": "B",
            "explanation": "Science is a systematic method of acquiring knowledge about the natural world through observation, hypothesis, and experimentation.",
            "pages": [1, 2],
        },
        {
            "q": "Which of the following is NOT a step in the scientific method?",
            "options": [
                "A) Observation",
                "B) Hypothesis",
                "C) Assumption without evidence",
                "D) Experimentation",
            ],
            "correct": "C",
            "explanation": "The scientific method relies on evidence-based steps: observation → hypothesis → experimentation → conclusion.",
            "pages": [3, 4],
        },
        {
            "q": "The SI unit of length is:",
            "options": ["A) Centimetre", "B) Metre", "C) Kilometre", "D) Foot"],
            "correct": "B",
            "explanation": "The International System of Units (SI) defines the metre (m) as the base unit of length.",
            "pages": [5, 6],
        },
        {
            "q": "A hypothesis that is repeatedly tested and confirmed becomes a:",
            "options": ["A) Fact", "B) Law", "C) Theory", "D) Guess"],
            "correct": "C",
            "explanation": "A well-tested, widely accepted hypothesis supported by extensive evidence becomes a scientific theory.",
            "pages": [3, 4],
        },
        {
            "q": "Which instrument is used to measure temperature?",
            "options": ["A) Barometer", "B) Thermometer", "C) Ammeter", "D) Voltmeter"],
            "correct": "B",
            "explanation": "A thermometer measures temperature. Clinical thermometers use mercury or digital sensors.",
            "pages": [7, 8],
        },
        {
            "q": "The correct way to read a measuring cylinder is:",
            "options": [
                "A) From the top of the meniscus",
                "B) At eye level from the bottom of the meniscus",
                "C) From any angle",
                "D) From below the cylinder",
            ],
            "correct": "B",
            "explanation": "To avoid parallax error, readings should be taken at eye level from the bottom of the meniscus.",
            "pages": [7, 8],
        },
        {
            "q": "Which of the following is a physical quantity?",
            "options": ["A) Beauty", "B) Taste", "C) Mass", "D) Emotion"],
            "correct": "C",
            "explanation": "Mass is a measurable physical quantity with units (kg). Beauty, taste, and emotion cannot be measured objectively.",
            "pages": [5, 6],
        },
        {
            "q": "Safety goggles are used in the laboratory to protect:",
            "options": ["A) Hands", "B) Feet", "C) Eyes", "D) Ears"],
            "correct": "C",
            "explanation": "Safety goggles protect eyes from chemical splashes, fumes, and flying particles during experiments.",
            "pages": [9, 10],
        },
        {
            "q": "1 kilometre equals:",
            "options": ["A) 100 metres", "B) 1000 metres", "C) 10000 metres", "D) 10 metres"],
            "correct": "B",
            "explanation": "1 km = 1000 m. The prefix 'kilo' means 1000.",
            "pages": [5, 6],
        },
        {
            "q": "An experiment must be:",
            "options": [
                "A) Done only once",
                "B) Reproducible by others",
                "C) Kept secret",
                "D) Based on personal belief",
            ],
            "correct": "B",
            "explanation": "Scientific experiments must be reproducible — other scientists should get similar results when repeating the experiment.",
            "pages": [3, 4],
        },
    ]

    bank["Cell: The Building Block of Life"] = [
        {
            "q": "Which organelle is called the 'powerhouse of the cell'?",
            "options": ["A) Nucleus", "B) Mitochondria", "C) Ribosome", "D) Golgi apparatus"],
            "correct": "B",
            "explanation": "Mitochondria generate ATP through cellular respiration — the cell's energy currency. Hence 'powerhouse'.",
            "pages": [20, 21],
        },
        {
            "q": "The cell wall is present in:",
            "options": [
                "A) Animal cells only",
                "B) Plant cells only",
                "C) Both plant and animal cells",
                "D) Neither",
            ],
            "correct": "B",
            "explanation": "Plant cells have a rigid cell wall made of cellulose outside the cell membrane. Animal cells lack it.",
            "pages": [18, 19],
        },
        {
            "q": "Which organelle is responsible for protein synthesis?",
            "options": ["A) Mitochondria", "B) Lysosomes", "C) Ribosomes", "D) Vacuoles"],
            "correct": "C",
            "explanation": "Ribosomes (both free and membrane-bound) are the sites of protein synthesis, translating mRNA.",
            "pages": [22, 23],
        },
        {
            "q": "The largest organelle in a plant cell is:",
            "options": ["A) Nucleus", "B) Mitochondria", "C) Central vacuole", "D) Chloroplast"],
            "correct": "C",
            "explanation": "The central vacuole in a mature plant cell can occupy up to 90% of the cell volume, storing water and maintaining turgor.",
            "pages": [24, 25],
        },
        {
            "q": "The membrane around the nucleus is called:",
            "options": ["A) Cell membrane", "B) Nuclear membrane", "C) Tonoplast", "D) Cell wall"],
            "correct": "B",
            "explanation": "The nuclear membrane (nuclear envelope) is a double membrane with pores that encloses the nucleus.",
            "pages": [20, 21],
        },
        {
            "q": "Which of the following is NOT found in animal cells?",
            "options": ["A) Mitochondria", "B) Chloroplast", "C) Nucleus", "D) Ribosome"],
            "correct": "B",
            "explanation": "Chloroplasts (site of photosynthesis) are found only in plant cells and some algae, not in animal cells.",
            "pages": [18, 19],
        },
        {
            "q": "Lysosomes contain:",
            "options": [
                "A) Starch",
                "B) Digestive enzymes",
                "C) Chlorophyll",
                "D) Genetic material",
            ],
            "correct": "B",
            "explanation": "Lysosomes contain hydrolytic enzymes that digest worn-out organelles and foreign materials — 'suicide bags'.",
            "pages": [22, 23],
        },
        {
            "q": "Osmosis is the movement of:",
            "options": [
                "A) Solute from low to high concentration",
                "B) Water from high to low water potential through a semipermeable membrane",
                "C) Gases across a membrane",
                "D) Solids through cell wall",
            ],
            "correct": "B",
            "explanation": "Osmosis is the net movement of water molecules from a region of high water potential to low water potential across a selectively permeable membrane.",
            "pages": [16, 17],
        },
        {
            "q": "DNA is found in:",
            "options": [
                "A) Cytoplasm only",
                "B) Nucleus and mitochondria",
                "C) Vacuole",
                "D) Cell wall",
            ],
            "correct": "B",
            "explanation": "Most DNA is in the nucleus (chromosomal DNA), but mitochondria also contain their own circular DNA.",
            "pages": [20, 21],
        },
        {
            "q": "The basic structural and functional unit of life is:",
            "options": ["A) Atom", "B) Molecule", "C) Cell", "D) Organ"],
            "correct": "C",
            "explanation": "The cell is the fundamental unit of life — the smallest unit that can carry out all life processes.",
            "pages": [16, 17],
        },
    ]

    bank["Tissues in Action"] = [
        {
            "q": "Which tissue covers the outer surface of the body?",
            "options": [
                "A) Connective tissue",
                "B) Epithelial tissue",
                "C) Muscular tissue",
                "D) Nervous tissue",
            ],
            "correct": "B",
            "explanation": "Epithelial tissue forms protective coverings on body surfaces and lining of organs.",
            "pages": [28, 29],
        },
        {
            "q": "Bone is a type of:",
            "options": [
                "A) Muscular tissue",
                "B) Epithelial tissue",
                "C) Connective tissue",
                "D) Nervous tissue",
            ],
            "correct": "C",
            "explanation": "Bone is a specialised connective tissue with calcium salts deposited in its matrix for rigidity.",
            "pages": [32, 33],
        },
        {
            "q": "Which muscle type is involuntary and found in the walls of internal organs?",
            "options": [
                "A) Skeletal muscle",
                "B) Cardiac muscle",
                "C) Smooth muscle",
                "D) Striated muscle",
            ],
            "correct": "C",
            "explanation": "Smooth (unstriated) muscles are involuntary, found in the walls of intestines, blood vessels, uterus, etc.",
            "pages": [34, 35],
        },
        {
            "q": "Neurons are cells of:",
            "options": [
                "A) Muscular tissue",
                "B) Connective tissue",
                "C) Epithelial tissue",
                "D) Nervous tissue",
            ],
            "correct": "D",
            "explanation": "Neurons are the structural and functional units of the nervous system, transmitting electrical impulses.",
            "pages": [36, 37],
        },
        {
            "q": "The tissue responsible for transport of food in plants is:",
            "options": ["A) Xylem", "B) Phloem", "C) Parenchyma", "D) Sclerenchyma"],
            "correct": "B",
            "explanation": "Phloem transports food (sucrose) synthesised during photosynthesis from leaves to other plant parts.",
            "pages": [30, 31],
        },
        {
            "q": "Meristematic tissue is found at:",
            "options": [
                "A) The tip of roots and shoots",
                "B) Bark of tree",
                "C) Mature leaves",
                "D) Heartwood",
            ],
            "correct": "A",
            "explanation": "Meristematic tissue (actively dividing cells) is found at root tips, shoot tips, and lateral meristems.",
            "pages": [28, 29],
        },
        {
            "q": "Blood is classified as a:",
            "options": [
                "A) Muscular tissue",
                "B) Epithelial tissue",
                "C) Connective tissue (fluid type)",
                "D) Nervous tissue",
            ],
            "correct": "C",
            "explanation": "Blood is a fluid connective tissue with cells (RBC, WBC, platelets) suspended in plasma (liquid matrix).",
            "pages": [32, 33],
        },
        {
            "q": "Which plant tissue provides flexibility?",
            "options": [
                "A) Sclerenchyma",
                "B) Collenchyma",
                "C) Parenchyma",
                "D) Meristematic tissue",
            ],
            "correct": "B",
            "explanation": "Collenchyma has irregularly thickened corners providing flexibility and support in growing stems and leaf stalks.",
            "pages": [30, 31],
        },
        {
            "q": "Cardiac muscle is found in:",
            "options": ["A) Arms", "B) Intestines", "C) Heart", "D) Skull"],
            "correct": "C",
            "explanation": "Cardiac muscle is involuntary striated muscle found exclusively in the heart, contracting rhythmically.",
            "pages": [34, 35],
        },
        {
            "q": "Cork cells are:",
            "options": [
                "A) Living and active",
                "B) Dead with suberin deposits",
                "C) Filled with chloroplasts",
                "D) Actively dividing",
            ],
            "correct": "B",
            "explanation": "Cork cells are dead, with cell walls thickened by suberin (a waxy substance), making bark waterproof.",
            "pages": [30, 31],
        },
    ]

    bank["Describing Motion Around Us"] = [
        {
            "q": "A body is said to be in uniform motion if it:",
            "options": [
                "A) Covers equal distances in equal intervals of time",
                "B) Moves in a curved path",
                "C) Has changing speed",
                "D) Accelerates constantly",
            ],
            "correct": "A",
            "explanation": "Uniform motion means equal distances are covered in equal time intervals — constant speed.",
            "pages": [40, 41],
        },
        {
            "q": "The SI unit of speed is:",
            "options": ["A) km/h", "B) m/s", "C) cm/s", "D) miles/hour"],
            "correct": "B",
            "explanation": "The SI unit of speed (and velocity) is metre per second (m/s).",
            "pages": [42, 43],
        },
        {
            "q": "The area under a velocity-time graph represents:",
            "options": ["A) Speed", "B) Acceleration", "C) Displacement", "D) Force"],
            "correct": "C",
            "explanation": "The area under a v-t graph gives displacement (distance with direction) during that time interval.",
            "pages": [46, 47],
        },
        {
            "q": "If a car moves at 20 m/s and stops in 4 seconds, its acceleration is:",
            "options": ["A) 5 m/s²", "B) -5 m/s²", "C) 80 m/s²", "D) -80 m/s²"],
            "correct": "B",
            "explanation": "a = (v-u)/t = (0-20)/4 = -5 m/s². Negative sign indicates deceleration (retardation).",
            "pages": [44, 45],
        },
        {
            "q": "Distance is a _____ quantity and displacement is a _____ quantity.",
            "options": [
                "A) Vector, scalar",
                "B) Scalar, vector",
                "C) Scalar, scalar",
                "D) Vector, vector",
            ],
            "correct": "B",
            "explanation": "Distance has only magnitude (scalar). Displacement has both magnitude and direction (vector).",
            "pages": [40, 41],
        },
        {
            "q": "The slope of a distance-time graph gives:",
            "options": ["A) Acceleration", "B) Distance", "C) Speed", "D) Time"],
            "correct": "C",
            "explanation": "Slope of distance-time graph = Δd/Δt = speed.",
            "pages": [46, 47],
        },
        {
            "q": "Which equation of motion relates velocity, acceleration and displacement?",
            "options": ["A) v = u + at", "B) s = ut + ½at²", "C) v² = u² + 2as", "D) All of these"],
            "correct": "C",
            "explanation": "v² = u² + 2as relates final velocity, initial velocity, acceleration, and displacement without involving time.",
            "pages": [48, 49],
        },
        {
            "q": "An object moving in a circular path with constant speed has:",
            "options": [
                "A) Zero acceleration",
                "B) Constant velocity",
                "C) Changing velocity",
                "D) No force acting on it",
            ],
            "correct": "C",
            "explanation": "Even at constant speed, direction changes continuously in circular motion — so velocity changes (centripetal acceleration).",
            "pages": [50, 51],
        },
        {
            "q": "The speedometer of a car measures:",
            "options": [
                "A) Average speed",
                "B) Instantaneous speed",
                "C) Acceleration",
                "D) Displacement",
            ],
            "correct": "B",
            "explanation": "A speedometer shows the instantaneous speed of the vehicle at that moment.",
            "pages": [42, 43],
        },
        {
            "q": "If a body starts from rest and has uniform acceleration 'a', the distance covered in time 't' is:",
            "options": ["A) at", "B) ½at²", "C) at²", "D) 2at²"],
            "correct": "B",
            "explanation": "From s = ut + ½at², when u = 0, s = ½at².",
            "pages": [48, 49],
        },
    ]

    bank["Exploring Mixtures and their Separation"] = [
        {
            "q": "A homogeneous mixture of two or more substances is called:",
            "options": ["A) Compound", "B) Solution", "C) Suspension", "D) Colloid"],
            "correct": "B",
            "explanation": "A solution is a homogeneous mixture where the solute is uniformly distributed in the solvent.",
            "pages": [52, 53],
        },
        {
            "q": "Which technique is used to separate a mixture of two miscible liquids?",
            "options": ["A) Filtration", "B) Distillation", "C) Decantation", "D) Handpicking"],
            "correct": "B",
            "explanation": "Distillation separates miscible liquids based on difference in their boiling points.",
            "pages": [56, 57],
        },
        {
            "q": "Tyndall effect is shown by:",
            "options": [
                "A) True solutions",
                "B) Colloidal solutions",
                "C) Pure solvents",
                "D) Gases",
            ],
            "correct": "B",
            "explanation": "Colloidal particles scatter light, making the beam visible — this is the Tyndall effect.",
            "pages": [54, 55],
        },
        {
            "q": "The size of particles in a suspension is:",
            "options": [
                "A) Less than 1 nm",
                "B) Between 1 nm and 100 nm",
                "C) Greater than 100 nm",
                "D) Exactly 50 nm",
            ],
            "correct": "C",
            "explanation": "Suspension particles are > 100 nm, visible to naked eye, settle down on standing, and scatter light.",
            "pages": [54, 55],
        },
        {
            "q": "Chromatography is used to separate:",
            "options": [
                "A) Insoluble solids from liquids",
                "B) Dyes or pigments in a mixture",
                "C) Gases from liquids",
                "D) Metals from ores",
            ],
            "correct": "B",
            "explanation": "Chromatography separates components based on their different rates of movement through a medium (e.g., separating dyes).",
            "pages": [58, 59],
        },
        {
            "q": "The component present in larger quantity in a solution is called:",
            "options": ["A) Solute", "B) Solvent", "C) Precipitate", "D) Residue"],
            "correct": "B",
            "explanation": "The solvent is present in larger quantity and dissolves the solute. Water is the 'universal solvent'.",
            "pages": [52, 53],
        },
        {
            "q": "Saturated solution at a given temperature:",
            "options": [
                "A) Can dissolve more solute",
                "B) Cannot dissolve more solute",
                "C) Has no solute",
                "D) Is always hot",
            ],
            "correct": "B",
            "explanation": "A saturated solution has dissolved the maximum amount of solute at that temperature — no more can dissolve.",
            "pages": [52, 53],
        },
        {
            "q": "Which method is used to obtain salt from sea water?",
            "options": ["A) Filtration", "B) Evaporation", "C) Distillation", "D) Sublimation"],
            "correct": "B",
            "explanation": "Solar evaporation of sea water in large open pans is used to obtain common salt (NaCl).",
            "pages": [56, 57],
        },
        {
            "q": "Alloys are examples of:",
            "options": [
                "A) Compounds",
                "B) Elements",
                "C) Homogeneous mixtures",
                "D) Heterogeneous mixtures",
            ],
            "correct": "C",
            "explanation": "Alloys (like brass, bronze, steel) are homogeneous mixtures of metals (or metal with non-metal).",
            "pages": [52, 53],
        },
        {
            "q": "Centrifugation is used to separate:",
            "options": [
                "A) Two miscible liquids",
                "B) Components of a colloidal solution",
                "C) Cream from milk",
                "D) Both B and C",
            ],
            "correct": "D",
            "explanation": "Centrifugation uses high-speed rotation to separate denser particles from lighter ones — used for milk cream and blood components.",
            "pages": [56, 57],
        },
    ]

    bank["How Forces Affect Motion"] = [
        {
            "q": "Newton's first law of motion is also known as:",
            "options": [
                "A) Law of acceleration",
                "B) Law of inertia",
                "C) Law of action-reaction",
                "D) Law of gravitation",
            ],
            "correct": "B",
            "explanation": "Newton's first law states that a body remains at rest or in uniform motion unless acted upon by an external force — the law of inertia.",
            "pages": [60, 61],
        },
        {
            "q": "The SI unit of force is:",
            "options": ["A) Dyne", "B) Newton", "C) Joule", "D) Pascal"],
            "correct": "B",
            "explanation": "Force is measured in Newton (N). 1 N = 1 kg × 1 m/s².",
            "pages": [62, 63],
        },
        {
            "q": "According to Newton's second law, F = ma. If force is doubled and mass remains constant:",
            "options": [
                "A) Acceleration halves",
                "B) Acceleration doubles",
                "C) Acceleration remains same",
                "D) Mass doubles",
            ],
            "correct": "B",
            "explanation": "F = ma. If F doubles and m is constant, a must also double.",
            "pages": [62, 63],
        },
        {
            "q": "Action and reaction forces:",
            "options": [
                "A) Act on the same body",
                "B) Act on different bodies",
                "C) Cancel each other",
                "D) Are equal in magnitude but act on the same body",
            ],
            "correct": "B",
            "explanation": "Newton's third law: action and reaction are equal and opposite but act on DIFFERENT bodies — they don't cancel.",
            "pages": [64, 65],
        },
        {
            "q": "Momentum is defined as:",
            "options": [
                "A) Mass × acceleration",
                "B) Mass × velocity",
                "C) Force × time",
                "D) Mass × distance",
            ],
            "correct": "B",
            "explanation": "Momentum (p) = mass (m) × velocity (v). It is a vector quantity measured in kg·m/s.",
            "pages": [66, 67],
        },
        {
            "q": "The conservation of momentum states that:",
            "options": [
                "A) Momentum can be created",
                "B) Total momentum before collision equals total momentum after collision in an isolated system",
                "C) Momentum is always zero",
                "D) Only kinetic energy is conserved",
            ],
            "correct": "B",
            "explanation": "In the absence of external forces, total momentum of a system remains constant before and after collision.",
            "pages": [68, 69],
        },
        {
            "q": "A cricket player moves his hands backward while catching a fast ball to:",
            "options": [
                "A) Increase the force of impact",
                "B) Reduce the time of impact",
                "C) Increase the time of impact, reducing force",
                "D) Show skill",
            ],
            "correct": "C",
            "explanation": "By pulling hands backward, the player increases the time over which momentum changes, reducing the force (F = Δp/Δt).",
            "pages": [64, 65],
        },
        {
            "q": "A passenger in a bus tends to fall backward when the bus starts suddenly because of:",
            "options": ["A) Friction", "B) Gravity", "C) Inertia of rest", "D) Inertia of motion"],
            "correct": "C",
            "explanation": "The lower body moves with the bus, but the upper body tends to remain at rest (inertia of rest) — causing backward fall.",
            "pages": [60, 61],
        },
        {
            "q": "If mass of a body is halved and velocity is doubled, its momentum:",
            "options": ["A) Remains same", "B) Doubles", "C) Halves", "D) Quadruples"],
            "correct": "A",
            "explanation": "p = mv. If m → m/2 and v → 2v, then p = (m/2)(2v) = mv = same.",
            "pages": [66, 67],
        },
        {
            "q": "Friction always:",
            "options": [
                "A) Helps motion",
                "B) Opposes relative motion",
                "C) Increases speed",
                "D) Acts perpendicular to surface",
            ],
            "correct": "B",
            "explanation": "Friction is a force that opposes the relative motion between two surfaces in contact.",
            "pages": [70, 71],
        },
    ]

    bank["Work, Energy, and Simple Machines"] = [
        {
            "q": "Work is done when:",
            "options": [
                "A) Force is applied but no displacement",
                "B) Force and displacement are in the same direction",
                "C) A person stands holding a heavy bag",
                "D) Earth revolves around the Sun (gravitational force perpendicular to motion)",
            ],
            "correct": "B",
            "explanation": "W = F·d·cos θ. Work is done when force causes displacement. If θ = 0°, W = Fd (maximum work).",
            "pages": [72, 73],
        },
        {
            "q": "The SI unit of energy is:",
            "options": ["A) Watt", "B) Newton", "C) Joule", "D) Pascal"],
            "correct": "C",
            "explanation": "Energy is measured in Joules (J). 1 J = 1 N × 1 m.",
            "pages": [74, 75],
        },
        {
            "q": "Kinetic energy of a body is given by:",
            "options": ["A) mgh", "B) ½mv²", "C) mv", "D) Fd"],
            "correct": "B",
            "explanation": "Kinetic energy = ½mv². It depends on mass and the square of velocity.",
            "pages": [76, 77],
        },
        {
            "q": "An object of mass 10 kg is at a height of 5 m. Its potential energy is (g = 10 m/s²):",
            "options": ["A) 50 J", "B) 500 J", "C) 100 J", "D) 5000 J"],
            "correct": "B",
            "explanation": "PE = mgh = 10 × 10 × 5 = 500 J.",
            "pages": [74, 75],
        },
        {
            "q": "The law of conservation of energy states:",
            "options": [
                "A) Energy can be created",
                "B) Energy can be destroyed",
                "C) Energy can neither be created nor destroyed, only transformed",
                "D) Total energy always increases",
            ],
            "correct": "C",
            "explanation": "Energy is always conserved — it transforms from one form to another. Total energy remains constant.",
            "pages": [78, 79],
        },
        {
            "q": "Power is defined as:",
            "options": [
                "A) Work × time",
                "B) Work / time",
                "C) Force × velocity",
                "D) Both B and C",
            ],
            "correct": "D",
            "explanation": "Power = Work/Time = F·v. Both definitions are equivalent. SI unit is Watt (W).",
            "pages": [80, 81],
        },
        {
            "q": "1 horsepower (HP) is equal to approximately:",
            "options": ["A) 746 watts", "B) 100 watts", "C) 500 watts", "D) 1000 watts"],
            "correct": "A",
            "explanation": "1 HP ≈ 746 watts. This is used to rate engines and motors.",
            "pages": [80, 81],
        },
        {
            "q": "A freely falling object has:",
            "options": [
                "A) Only potential energy",
                "B) Only kinetic energy",
                "C) Both PE and KE that interchange",
                "D) No energy",
            ],
            "correct": "C",
            "explanation": "As an object falls, PE decreases and KE increases. Total mechanical energy (PE + KE) remains constant.",
            "pages": [78, 79],
        },
        {
            "q": "Which simple machine can change the direction of force?",
            "options": ["A) Inclined plane", "B) Pulley", "C) Wedge", "D) Screw"],
            "correct": "B",
            "explanation": "A fixed pulley changes the direction of the applied force, making it easier to lift loads.",
            "pages": [82, 83],
        },
        {
            "q": "Commercial unit of energy is:",
            "options": ["A) Joule", "B) Calorie", "C) Kilowatt-hour", "D) Erg"],
            "correct": "C",
            "explanation": "1 kWh = 3.6 × 10⁶ J. Electricity consumption is measured in kWh (units).",
            "pages": [80, 81],
        },
    ]

    bank["Journey Inside the Atom"] = [
        {
            "q": "Who discovered the electron?",
            "options": ["A) Rutherford", "B) J.J. Thomson", "C) Bohr", "D) Dalton"],
            "correct": "B",
            "explanation": "J.J. Thomson discovered electrons in 1897 through cathode ray experiments.",
            "pages": [84, 85],
        },
        {
            "q": "The nucleus of an atom contains:",
            "options": [
                "A) Only protons",
                "B) Only neutrons",
                "C) Protons and neutrons",
                "D) Electrons and protons",
            ],
            "correct": "C",
            "explanation": "The nucleus contains protons (positive) and neutrons (neutral). Electrons orbit outside.",
            "pages": [86, 87],
        },
        {
            "q": "Rutherford's alpha particle scattering experiment proved that:",
            "options": [
                "A) Electrons are inside the nucleus",
                "B) Most of the atom is empty space",
                "C) Atoms are indivisible",
                "D) Neutrons are outside the nucleus",
            ],
            "correct": "B",
            "explanation": "Most alpha particles passed through the gold foil, proving that atoms are mostly empty space with a tiny dense nucleus.",
            "pages": [86, 87],
        },
        {
            "q": "The maximum number of electrons in the second shell (L-shell) is:",
            "options": ["A) 2", "B) 8", "C) 18", "D) 32"],
            "correct": "B",
            "explanation": "Maximum electrons in shell n = 2n². For L-shell (n=2): 2(2²) = 8.",
            "pages": [88, 89],
        },
        {
            "q": "Isotopes have:",
            "options": [
                "A) Same atomic number, different mass number",
                "B) Different atomic number, same mass number",
                "C) Same number of neutrons",
                "D) Different chemical properties",
            ],
            "correct": "A",
            "explanation": "Isotopes have same number of protons (atomic number) but different neutrons (different mass number).",
            "pages": [90, 91],
        },
        {
            "q": "The atomic number of an element is equal to:",
            "options": [
                "A) Number of neutrons",
                "B) Number of protons",
                "C) Number of protons + neutrons",
                "D) Number of electrons in ions",
            ],
            "correct": "B",
            "explanation": "Atomic number (Z) = number of protons in the nucleus. It uniquely identifies an element.",
            "pages": [86, 87],
        },
        {
            "q": "Thomson's model of atom is called:",
            "options": [
                "A) Planetary model",
                "B) Nuclear model",
                "C) Plum pudding model",
                "D) Bohr's model",
            ],
            "correct": "C",
            "explanation": "Thomson proposed that electrons are embedded in a positive sphere like plums in a pudding — 'plum pudding model'.",
            "pages": [84, 85],
        },
        {
            "q": "Valency of an element with electronic configuration 2,8,3 is:",
            "options": ["A) 2", "B) 3", "C) 5", "D) 8"],
            "correct": "B",
            "explanation": "Valency = electrons in outermost shell (if ≤ 4) = 3. The element tends to lose 3 electrons.",
            "pages": [88, 89],
        },
        {
            "q": "Isobars are atoms of:",
            "options": [
                "A) Same element with different mass",
                "B) Different elements with same mass number",
                "C) Same element with same mass",
                "D) Different elements with different mass",
            ],
            "correct": "B",
            "explanation": "Isobars have same mass number but different atomic numbers (different elements). E.g., ⁴⁰Ca and ⁴⁰Ar.",
            "pages": [90, 91],
        },
        {
            "q": "The charge on an electron is:",
            "options": ["A) +1.6 × 10⁻¹⁹ C", "B) -1.6 × 10⁻¹⁹ C", "C) 0", "D) -1.6 × 10⁻²⁰ C"],
            "correct": "B",
            "explanation": "An electron carries a negative charge of 1.6 × 10⁻¹⁹ coulombs.",
            "pages": [84, 85],
        },
    ]

    bank["Atomic Foundations of Matter"] = [
        {
            "q": "The law of constant proportions was given by:",
            "options": ["A) Dalton", "B) Proust", "C) Lavoisier", "D) Avogadro"],
            "correct": "B",
            "explanation": "Joseph Proust stated that a compound always contains the same elements in the same proportion by mass.",
            "pages": [92, 93],
        },
        {
            "q": "One mole of any substance contains:",
            "options": [
                "A) 6.022 × 10²² particles",
                "B) 6.022 × 10²³ particles",
                "C) 6.022 × 10²⁴ particles",
                "D) 6.022 × 10²¹ particles",
            ],
            "correct": "B",
            "explanation": "One mole = Avogadro's number = 6.022 × 10²³ particles (atoms, molecules, or ions).",
            "pages": [96, 97],
        },
        {
            "q": "The chemical formula of water is H₂O. This means:",
            "options": [
                "A) 1 atom of H and 2 atoms of O",
                "B) 2 atoms of H and 1 atom of O",
                "C) 2 molecules of H and 1 molecule of O",
                "D) 1 molecule of H and 2 molecules of O",
            ],
            "correct": "B",
            "explanation": "H₂O means each molecule has 2 hydrogen atoms and 1 oxygen atom.",
            "pages": [94, 95],
        },
        {
            "q": "The atomic mass of oxygen is:",
            "options": ["A) 8 u", "B) 16 u", "C) 32 u", "D) 12 u"],
            "correct": "B",
            "explanation": "The atomic mass of oxygen is 16 u (atomic mass units). O₂ molecule has molecular mass 32 u.",
            "pages": [94, 95],
        },
        {
            "q": "Which of the following has the highest molecular mass?",
            "options": ["A) H₂O (18 u)", "B) CO₂ (44 u)", "C) H₂SO₄ (98 u)", "D) NaCl (58.5 u)"],
            "correct": "C",
            "explanation": "H₂SO₄: 2(1) + 32 + 4(16) = 98 u — highest among the options.",
            "pages": [96, 97],
        },
        {
            "q": "The molecular formula of glucose is:",
            "options": ["A) C₆H₆O₆", "B) C₆H₁₂O₆", "C) C₆H₁₀O₅", "D) CH₂O"],
            "correct": "B",
            "explanation": "Glucose has the molecular formula C₆H₁₂O₆ with molecular mass = 180 u.",
            "pages": [94, 95],
        },
        {
            "q": "Dalton's atomic theory stated that:",
            "options": [
                "A) Atoms are divisible",
                "B) Atoms of the same element are different",
                "C) Atoms are the smallest indivisible particles",
                "D) Atoms have a nucleus",
            ],
            "correct": "C",
            "explanation": "Dalton proposed atoms as indivisible particles (later disproven by discovery of subatomic particles).",
            "pages": [92, 93],
        },
        {
            "q": "The formula unit mass of NaCl is:",
            "options": ["A) 23 u", "B) 35.5 u", "C) 58.5 u", "D) 44 u"],
            "correct": "C",
            "explanation": "NaCl: Na (23) + Cl (35.5) = 58.5 u.",
            "pages": [94, 95],
        },
        {
            "q": "Polyatomic ions are:",
            "options": [
                "A) Single atoms with charge",
                "B) Groups of atoms carrying a net charge",
                "C) Neutral molecules",
                "D) Uncharged atom groups",
            ],
            "correct": "B",
            "explanation": "Polyatomic ions like SO₄²⁻, NO₃⁻, NH₄⁺ are groups of atoms that carry a net charge.",
            "pages": [94, 95],
        },
        {
            "q": "The molar mass of CO₂ is:",
            "options": ["A) 28 g/mol", "B) 44 g/mol", "C) 16 g/mol", "D) 32 g/mol"],
            "correct": "B",
            "explanation": "CO₂: C (12) + 2×O (32) = 44 g/mol.",
            "pages": [96, 97],
        },
    ]

    bank["Sound Waves: Characteristics and Applications"] = [
        {
            "q": "Sound travels fastest in:",
            "options": ["A) Air", "B) Water", "C) Steel", "D) Vacuum"],
            "correct": "C",
            "explanation": "Sound travels fastest in solids (steel: ~5960 m/s) because molecules are closest together.",
            "pages": [98, 99],
        },
        {
            "q": "The unit of frequency is:",
            "options": ["A) Metre", "B) Second", "C) Hertz", "D) Decibel"],
            "correct": "C",
            "explanation": "Frequency is measured in Hertz (Hz). 1 Hz = 1 vibration per second.",
            "pages": [100, 101],
        },
        {
            "q": "An echo is heard when sound reflects from a surface at a minimum distance of:",
            "options": ["A) 8.5 m", "B) 17 m", "C) 34 m", "D) 51 m"],
            "correct": "B",
            "explanation": "For an echo, minimum distance = speed × time / 2 = 340 × 0.1 / 2 = 17 m (persistence of hearing = 0.1 s).",
            "pages": [104, 105],
        },
        {
            "q": "Ultrasound has frequency:",
            "options": [
                "A) Less than 20 Hz",
                "B) Between 20 Hz and 20,000 Hz",
                "C) Greater than 20,000 Hz",
                "D) Exactly 20,000 Hz",
            ],
            "correct": "C",
            "explanation": "Ultrasound has frequency > 20 kHz, beyond human hearing range. Used in medical imaging (USG) and SONAR.",
            "pages": [106, 107],
        },
        {
            "q": "Sound cannot travel through:",
            "options": ["A) Solids", "B) Liquids", "C) Gases", "D) Vacuum"],
            "correct": "D",
            "explanation": "Sound is a mechanical wave that needs a medium (solid, liquid, gas) for propagation. Vacuum has no particles.",
            "pages": [98, 99],
        },
        {
            "q": "The loudness of sound depends on:",
            "options": ["A) Frequency", "B) Amplitude", "C) Wavelength", "D) Speed"],
            "correct": "B",
            "explanation": "Loudness is determined by the amplitude of vibration. Greater amplitude → louder sound.",
            "pages": [102, 103],
        },
        {
            "q": "Pitch of a sound is determined by its:",
            "options": ["A) Amplitude", "B) Frequency", "C) Speed", "D) Wavelength"],
            "correct": "B",
            "explanation": "Pitch is the perception of frequency. Higher frequency → higher pitch (shriller sound).",
            "pages": [102, 103],
        },
        {
            "q": "SONAR stands for:",
            "options": [
                "A) Sound Navigation and Ranging",
                "B) Solar Navigation and Ranging",
                "C) Sound Network and Radar",
                "D) Super Omnidirectional Navigation and Radar",
            ],
            "correct": "A",
            "explanation": "SONAR (Sound Navigation And Ranging) uses ultrasonic waves to measure ocean depth and detect underwater objects.",
            "pages": [106, 107],
        },
        {
            "q": "The speed of sound in air at room temperature is approximately:",
            "options": ["A) 3 × 10⁸ m/s", "B) 1500 m/s", "C) 340 m/s", "D) 100 m/s"],
            "correct": "C",
            "explanation": "Sound travels at approximately 340 m/s in air at 20°C. (Speed increases with temperature.)",
            "pages": [98, 99],
        },
        {
            "q": "Noise pollution can cause:",
            "options": [
                "A) Hearing loss",
                "B) High blood pressure",
                "C) Stress and anxiety",
                "D) All of the above",
            ],
            "correct": "D",
            "explanation": "Prolonged noise above 85 dB causes hearing loss, increased blood pressure, stress, and other health issues.",
            "pages": [108, 109],
        },
    ]

    bank["Reproduction: How Life Continues"] = [
        {
            "q": "Binary fission occurs in:",
            "options": ["A) Amoeba", "B) Hydra", "C) Planaria", "D) Yeast"],
            "correct": "A",
            "explanation": "Amoeba reproduces asexually by binary fission — the cell divides into two equal daughter cells.",
            "pages": [110, 111],
        },
        {
            "q": "Budding is observed in:",
            "options": ["A) Amoeba", "B) Hydra", "C) Spirogyra", "D) Fern"],
            "correct": "B",
            "explanation": "In Hydra, a bud develops as an outgrowth and eventually detaches to form a new organism.",
            "pages": [110, 111],
        },
        {
            "q": "Vegetative propagation in potato occurs through:",
            "options": ["A) Stem tubers (eyes)", "B) Leaves", "C) Seeds", "D) Roots"],
            "correct": "A",
            "explanation": "Potato tubers have 'eyes' (buds) that sprout to grow into new plants — vegetative propagation.",
            "pages": [112, 113],
        },
        {
            "q": "Pollen grains are produced in:",
            "options": ["A) Ovary", "B) Stigma", "C) Anther", "D) Style"],
            "correct": "C",
            "explanation": "The anther (part of stamen) produces pollen grains containing male gametes.",
            "pages": [114, 115],
        },
        {
            "q": "Spore formation is seen in:",
            "options": ["A) Rhizopus (bread mould)", "B) Rose plant", "C) Mango tree", "D) Dog"],
            "correct": "A",
            "explanation": "Rhizopus reproduces asexually by forming spores in sporangia, which germinate under favourable conditions.",
            "pages": [110, 111],
        },
        {
            "q": "Which is not an advantage of vegetative propagation?",
            "options": [
                "A) Faster reproduction",
                "B) Maintains genetic uniformity",
                "C) Creates genetic variation",
                "D) No need for seeds",
            ],
            "correct": "C",
            "explanation": "Vegetative propagation produces clones — genetically identical organisms. No variation is introduced.",
            "pages": [112, 113],
        },
        {
            "q": "In flowers, the female reproductive part is:",
            "options": ["A) Stamen", "B) Pistil (carpel)", "C) Sepal", "D) Petal"],
            "correct": "B",
            "explanation": "The pistil (carpel) is the female part consisting of stigma, style, and ovary.",
            "pages": [114, 115],
        },
        {
            "q": "Self-pollination occurs when:",
            "options": [
                "A) Pollen from one flower reaches stigma of another flower on a different plant",
                "B) Pollen from anther reaches stigma of the same flower",
                "C) Pollen is transferred by wind only",
                "D) Insects carry pollen",
            ],
            "correct": "B",
            "explanation": "Self-pollination transfers pollen from anther to stigma of the same flower or another flower on the same plant.",
            "pages": [114, 115],
        },
        {
            "q": "After fertilization, the ovule develops into:",
            "options": ["A) Fruit", "B) Seed", "C) Pollen", "D) Embryo sac"],
            "correct": "B",
            "explanation": "The fertilized ovule develops into a seed, while the ovary develops into a fruit.",
            "pages": [116, 117],
        },
        {
            "q": "Fragmentation is a mode of reproduction in:",
            "options": ["A) Mushroom", "B) Spirogyra", "C) Hydra", "D) Amoeba"],
            "correct": "B",
            "explanation": "Spirogyra (filamentous algae) breaks into fragments, each growing into a new filament — fragmentation.",
            "pages": [110, 111],
        },
    ]

    bank["Patterns in Life: Diversity and Classification"] = [
        {
            "q": "The two-kingdom classification was proposed by:",
            "options": ["A) Whittaker", "B) Linnaeus", "C) Aristotle", "D) Haeckel"],
            "correct": "B",
            "explanation": "Carl Linnaeus proposed the two-kingdom classification: Plantae and Animalia.",
            "pages": [118, 119],
        },
        {
            "q": "Organisms that lack a well-defined nucleus are called:",
            "options": ["A) Eukaryotes", "B) Prokaryotes", "C) Protists", "D) Fungi"],
            "correct": "B",
            "explanation": "Prokaryotes (bacteria, cyanobacteria) lack a membrane-bound nucleus. Their DNA is in the nucleoid region.",
            "pages": [120, 121],
        },
        {
            "q": "Mushroom belongs to kingdom:",
            "options": ["A) Plantae", "B) Animalia", "C) Fungi", "D) Protista"],
            "correct": "C",
            "explanation": "Mushrooms are fungi — heterotrophic organisms that absorb nutrients from decaying organic matter.",
            "pages": [122, 123],
        },
        {
            "q": "Which of the following is NOT a vertebrate?",
            "options": ["A) Fish", "B) Frog", "C) Earthworm", "D) Snake"],
            "correct": "C",
            "explanation": "Earthworm is an invertebrate (phylum Annelida). Fish, frog, and snake have backbones (vertebrates).",
            "pages": [126, 127],
        },
        {
            "q": "Bryophytes are also called:",
            "options": [
                "A) Vascular plants",
                "B) Amphibians of the plant kingdom",
                "C) Flowering plants",
                "D) Seed-bearing plants",
            ],
            "correct": "B",
            "explanation": "Bryophytes (mosses, liverworts) need water for reproduction, like amphibians — hence 'amphibians of plant kingdom'.",
            "pages": [124, 125],
        },
        {
            "q": "The binomial nomenclature system was given by:",
            "options": ["A) Darwin", "B) Lamarck", "C) Linnaeus", "D) Mendel"],
            "correct": "C",
            "explanation": "Linnaeus introduced binomial nomenclature — every organism has a two-part Latin name (Genus species).",
            "pages": [118, 119],
        },
        {
            "q": "Animals with jointed legs belong to phylum:",
            "options": ["A) Mollusca", "B) Arthropoda", "C) Annelida", "D) Echinodermata"],
            "correct": "B",
            "explanation": "Arthropoda ('jointed feet') includes insects, spiders, crustaceans — the largest animal phylum.",
            "pages": [126, 127],
        },
        {
            "q": "Gymnosperms differ from angiosperms in that they:",
            "options": [
                "A) Have flowers",
                "B) Have naked seeds (not enclosed in fruit)",
                "C) Are non-vascular",
                "D) Are aquatic",
            ],
            "correct": "B",
            "explanation": "Gymnosperms (pines, cycads) have naked seeds not enclosed in a fruit, unlike angiosperms (flowering plants).",
            "pages": [124, 125],
        },
        {
            "q": "Which group of animals is cold-blooded (ectothermic)?",
            "options": ["A) Birds", "B) Mammals", "C) Reptiles", "D) Primates"],
            "correct": "C",
            "explanation": "Reptiles are cold-blooded — their body temperature varies with the environment (ectothermic).",
            "pages": [128, 129],
        },
        {
            "q": "The five-kingdom classification was proposed by:",
            "options": ["A) Linnaeus", "B) Haeckel", "C) Whittaker", "D) Aristotle"],
            "correct": "C",
            "explanation": "R.H. Whittaker (1969) proposed five kingdoms: Monera, Protista, Fungi, Plantae, Animalia.",
            "pages": [120, 121],
        },
    ]

    bank["Earth as a System: Energy, Matter, and Life"] = [
        {
            "q": "The atmosphere of Earth primarily consists of:",
            "options": [
                "A) Oxygen and carbon dioxide",
                "B) Nitrogen and oxygen",
                "C) Hydrogen and helium",
                "D) Carbon dioxide and methane",
            ],
            "correct": "B",
            "explanation": "Earth's atmosphere is ~78% nitrogen and ~21% oxygen, with trace amounts of other gases.",
            "pages": [130, 131],
        },
        {
            "q": "The water cycle involves:",
            "options": [
                "A) Evaporation, condensation, and precipitation",
                "B) Only evaporation",
                "C) Only rainfall",
                "D) Only condensation",
            ],
            "correct": "A",
            "explanation": "The water cycle involves evaporation → condensation → precipitation → collection, continuously cycling water.",
            "pages": [132, 133],
        },
        {
            "q": "The greenhouse effect is caused mainly by:",
            "options": ["A) Oxygen", "B) Nitrogen", "C) Carbon dioxide and methane", "D) Argon"],
            "correct": "C",
            "explanation": "CO₂ and methane trap infrared radiation re-emitted by Earth's surface, warming the atmosphere.",
            "pages": [134, 135],
        },
        {
            "q": "Ozone (O₃) in the stratosphere protects us from:",
            "options": [
                "A) Visible light",
                "B) Infrared radiation",
                "C) Ultraviolet radiation",
                "D) Radio waves",
            ],
            "correct": "C",
            "explanation": "The ozone layer absorbs harmful UV radiation from the Sun, protecting life on Earth.",
            "pages": [134, 135],
        },
        {
            "q": "Nitrogen fixation is done by:",
            "options": [
                "A) All plants",
                "B) Certain bacteria (e.g., Rhizobium)",
                "C) Animals",
                "D) Fungi only",
            ],
            "correct": "B",
            "explanation": "Nitrogen-fixing bacteria like Rhizobium (in legume root nodules) convert atmospheric N₂ to ammonia.",
            "pages": [132, 133],
        },
        {
            "q": "Soil erosion can be prevented by:",
            "options": [
                "A) Deforestation",
                "B) Overgrazing",
                "C) Afforestation and terrace farming",
                "D) Removing vegetation",
            ],
            "correct": "C",
            "explanation": "Planting trees (afforestation) and terrace farming prevent soil erosion by binding soil and reducing water flow.",
            "pages": [136, 137],
        },
        {
            "q": "The carbon cycle involves:",
            "options": [
                "A) Only photosynthesis",
                "B) Photosynthesis, respiration, decomposition, and combustion",
                "C) Only combustion",
                "D) Only respiration",
            ],
            "correct": "B",
            "explanation": "Carbon cycles through photosynthesis (CO₂ → organic), respiration, decomposition, and fossil fuel combustion.",
            "pages": [132, 133],
        },
        {
            "q": "Acid rain is caused by:",
            "options": [
                "A) CO₂ only",
                "B) SO₂ and NO₂ dissolving in rainwater",
                "C) O₂ in excess",
                "D) Water vapour",
            ],
            "correct": "B",
            "explanation": "SO₂ and NOₓ from industrial emissions dissolve in rainwater forming sulphuric and nitric acids — acid rain.",
            "pages": [134, 135],
        },
        {
            "q": "Renewable resources include:",
            "options": ["A) Coal", "B) Petroleum", "C) Solar energy", "D) Natural gas"],
            "correct": "C",
            "explanation": "Solar energy is renewable — continuously available from the Sun. Coal, petroleum, and gas are non-renewable.",
            "pages": [136, 137],
        },
        {
            "q": "The topsoil is the most important layer for plant growth because it:",
            "options": [
                "A) Contains rocks",
                "B) Contains humus and minerals",
                "C) Is the deepest",
                "D) Has no organisms",
            ],
            "correct": "B",
            "explanation": "Topsoil is rich in humus (decomposed organic matter) and minerals, providing nutrients for plant growth.",
            "pages": [136, 137],
        },
    ]

    # ===================== CLASS 10 MATHEMATICS =====================
    bank["Real Numbers"] = [
        {
            "q": "The HCF of 12 and 18 using Euclid's division algorithm is:",
            "options": ["A) 2", "B) 3", "C) 6", "D) 36"],
            "correct": "C",
            "explanation": "18 = 12 × 1 + 6; 12 = 6 × 2 + 0. HCF = 6.",
            "pages": [2, 3],
        },
        {
            "q": "The fundamental theorem of arithmetic states that every composite number can be expressed as:",
            "options": [
                "A) Sum of primes",
                "B) Product of primes uniquely",
                "C) Difference of primes",
                "D) Ratio of primes",
            ],
            "correct": "B",
            "explanation": "Every composite number has a unique prime factorisation (up to the order of factors).",
            "pages": [4, 5],
        },
        {
            "q": "√2 is:",
            "options": ["A) Rational", "B) Irrational", "C) Natural number", "D) Integer"],
            "correct": "B",
            "explanation": "√2 cannot be expressed as p/q (proven by contradiction). It is irrational.",
            "pages": [8, 9],
        },
        {
            "q": "The decimal expansion of a rational number p/q terminates if q has factors:",
            "options": [
                "A) Only 2 and 5",
                "B) Only 3 and 7",
                "C) Any prime factors",
                "D) Only 2 and 3",
            ],
            "correct": "A",
            "explanation": "A rational number has terminating decimal expansion iff the denominator (in simplest form) has only 2 and 5 as prime factors.",
            "pages": [10, 11],
        },
        {
            "q": "LCM(6, 8) × HCF(6, 8) = ?",
            "options": ["A) 48", "B) 24", "C) 36", "D) 14"],
            "correct": "A",
            "explanation": "LCM × HCF = product of numbers = 6 × 8 = 48. (LCM=24, HCF=2, 24×2=48).",
            "pages": [6, 7],
        },
        {
            "q": "If HCF(a, b) = 1, then a and b are:",
            "options": [
                "A) Even numbers",
                "B) Co-prime",
                "C) Prime numbers",
                "D) Composite numbers",
            ],
            "correct": "B",
            "explanation": "Two numbers with HCF = 1 are co-prime (no common factor other than 1). They need not be prime.",
            "pages": [6, 7],
        },
        {
            "q": "The number 0.3333... is:",
            "options": [
                "A) Irrational",
                "B) Rational (= 1/3)",
                "C) Neither rational nor irrational",
                "D) A natural number",
            ],
            "correct": "B",
            "explanation": "0.333... = 1/3, which is a ratio of two integers. Hence rational.",
            "pages": [10, 11],
        },
        {
            "q": "The product of a non-zero rational and an irrational number is:",
            "options": [
                "A) Always rational",
                "B) Always irrational",
                "C) Sometimes rational",
                "D) Always zero",
            ],
            "correct": "B",
            "explanation": "The product of a non-zero rational number with an irrational number is always irrational.",
            "pages": [8, 9],
        },
        {
            "q": "For any two positive integers a and b, a = bq + r, then r satisfies:",
            "options": ["A) 0 < r < b", "B) 0 ≤ r < b", "C) 0 ≤ r ≤ b", "D) r > b"],
            "correct": "B",
            "explanation": "Euclid's division lemma: a = bq + r where 0 ≤ r < b.",
            "pages": [2, 3],
        },
        {
            "q": "5 − √3 is:",
            "options": [
                "A) A rational number",
                "B) An irrational number",
                "C) A natural number",
                "D) An integer",
            ],
            "correct": "B",
            "explanation": "Since √3 is irrational, 5 − √3 (difference of rational and irrational) is irrational.",
            "pages": [8, 9],
        },
    ]

    bank["Polynomials"] = [
        {
            "q": "The zeroes of p(x) = x² − 5x + 6 are:",
            "options": ["A) 2 and 3", "B) -2 and -3", "C) 1 and 6", "D) -1 and -6"],
            "correct": "A",
            "explanation": "x² − 5x + 6 = (x−2)(x−3). Zeroes are x = 2 and x = 3.",
            "pages": [14, 15],
        },
        {
            "q": "If α and β are zeroes of x² − 7x + 10, then α + β = ?",
            "options": ["A) 10", "B) 7", "C) -7", "D) -10"],
            "correct": "B",
            "explanation": "For ax² + bx + c, sum of zeroes = −b/a = −(−7)/1 = 7.",
            "pages": [16, 17],
        },
        {
            "q": "A polynomial of degree 3 is called:",
            "options": ["A) Linear", "B) Quadratic", "C) Cubic", "D) Quartic"],
            "correct": "C",
            "explanation": "Degree 1 = linear, degree 2 = quadratic, degree 3 = cubic, degree 4 = quartic.",
            "pages": [12, 13],
        },
        {
            "q": "The number of zeroes of a quadratic polynomial is at most:",
            "options": ["A) 1", "B) 2", "C) 3", "D) 0"],
            "correct": "B",
            "explanation": "A polynomial of degree n has at most n zeroes. Quadratic (degree 2) → at most 2 zeroes.",
            "pages": [14, 15],
        },
        {
            "q": "If one zero of 2x² − 5x + k is 1, then k = ?",
            "options": ["A) 2", "B) 3", "C) 5", "D) -3"],
            "correct": "B",
            "explanation": "If x=1 is a zero: 2(1)² − 5(1) + k = 0 → 2 − 5 + k = 0 → k = 3.",
            "pages": [16, 17],
        },
        {
            "q": "The graph of a quadratic polynomial is a:",
            "options": ["A) Straight line", "B) Circle", "C) Parabola", "D) Hyperbola"],
            "correct": "C",
            "explanation": "The graph of y = ax² + bx + c is always a parabola (opening up if a > 0, down if a < 0).",
            "pages": [14, 15],
        },
        {
            "q": "Product of zeroes of 3x² + 5x − 2 is:",
            "options": ["A) 5/3", "B) -5/3", "C) -2/3", "D) 2/3"],
            "correct": "C",
            "explanation": "Product of zeroes = c/a = −2/3.",
            "pages": [16, 17],
        },
        {
            "q": "Division algorithm for polynomials states:",
            "options": [
                "A) p(x) = g(x) × q(x) + r(x)",
                "B) p(x) = g(x) + q(x)",
                "C) p(x) = g(x) − r(x)",
                "D) p(x) = g(x) / q(x)",
            ],
            "correct": "A",
            "explanation": "Dividend = Divisor × Quotient + Remainder, where degree of r(x) < degree of g(x).",
            "pages": [18, 19],
        },
        {
            "q": "The zeroes of x² − 4 are:",
            "options": ["A) 2 and 2", "B) 2 and -2", "C) 4 and -4", "D) 0 and 4"],
            "correct": "B",
            "explanation": "x² − 4 = (x−2)(x+2). Zeroes: x = 2 and x = −2.",
            "pages": [14, 15],
        },
        {
            "q": "If α and β are zeroes of x² + x − 6, then αβ = ?",
            "options": ["A) 1", "B) -1", "C) -6", "D) 6"],
            "correct": "C",
            "explanation": "Product of zeroes = c/a = −6/1 = −6.",
            "pages": [16, 17],
        },
    ]

    bank["Pair of Linear Equations in Two Variables"] = [
        {
            "q": "The pair of equations x + y = 5 and 2x + 2y = 10 is:",
            "options": [
                "A) Inconsistent",
                "B) Consistent with unique solution",
                "C) Consistent with infinite solutions",
                "D) None of these",
            ],
            "correct": "C",
            "explanation": "a₁/a₂ = b₁/b₂ = c₁/c₂ (1/2 = 1/2 = 5/10). The lines are coincident — infinitely many solutions.",
            "pages": [20, 21],
        },
        {
            "q": "Solve: x + y = 10, x − y = 4. The values of x and y are:",
            "options": ["A) x=7, y=3", "B) x=3, y=7", "C) x=5, y=5", "D) x=6, y=4"],
            "correct": "A",
            "explanation": "Adding: 2x = 14, x = 7. Substituting: y = 10 − 7 = 3.",
            "pages": [22, 23],
        },
        {
            "q": "For consistent equations with a unique solution:",
            "options": [
                "A) a₁/a₂ ≠ b₁/b₂",
                "B) a₁/a₂ = b₁/b₂ = c₁/c₂",
                "C) a₁/a₂ = b₁/b₂ ≠ c₁/c₂",
                "D) None of these",
            ],
            "correct": "A",
            "explanation": "When a₁/a₂ ≠ b₁/b₂, lines intersect at exactly one point — unique solution.",
            "pages": [20, 21],
        },
        {
            "q": "The graphical representation of inconsistent equations is:",
            "options": [
                "A) Intersecting lines",
                "B) Parallel lines",
                "C) Coincident lines",
                "D) Perpendicular lines",
            ],
            "correct": "B",
            "explanation": "Inconsistent equations (no solution) are represented by parallel lines that never meet.",
            "pages": [20, 21],
        },
        {
            "q": "If 2x + 3y = 12 and 4x + 6y = 24, the system has:",
            "options": [
                "A) No solution",
                "B) Unique solution",
                "C) Infinitely many solutions",
                "D) Two solutions",
            ],
            "correct": "C",
            "explanation": "2/4 = 3/6 = 12/24 → ½ = ½ = ½. Lines are coincident — infinitely many solutions.",
            "pages": [20, 21],
        },
        {
            "q": "Substitution method involves:",
            "options": [
                "A) Adding equations",
                "B) Expressing one variable in terms of other and substituting",
                "C) Graphing both equations",
                "D) Multiplying equations",
            ],
            "correct": "B",
            "explanation": "In substitution, solve one equation for a variable, then substitute into the other equation.",
            "pages": [24, 25],
        },
        {
            "q": "The solution of x + y = 7 and xy = 12 gives x and y as:",
            "options": ["A) 3 and 4", "B) 2 and 5", "C) 1 and 6", "D) -3 and -4"],
            "correct": "A",
            "explanation": "x + y = 7, xy = 12. The values 3 and 4 satisfy both: 3+4=7, 3×4=12.",
            "pages": [22, 23],
        },
        {
            "q": "Cross-multiplication method gives the solution of a₁x + b₁y + c₁ = 0 and a₂x + b₂y + c₂ = 0 as:",
            "options": [
                "A) x/(b₁c₂−b₂c₁) = y/(c₁a₂−c₂a₁) = 1/(a₁b₂−a₂b₁)",
                "B) x = a₁+a₂, y = b₁+b₂",
                "C) x = c₁/a₁, y = c₂/a₂",
                "D) None",
            ],
            "correct": "A",
            "explanation": "The cross-multiplication formula gives a systematic algebraic solution for linear equation pairs.",
            "pages": [26, 27],
        },
        {
            "q": "The number of solutions of the pair x = 3 and y = 5 is:",
            "options": ["A) 0", "B) 1", "C) 2", "D) Infinite"],
            "correct": "B",
            "explanation": "x = 3 and y = 5 are two lines (one vertical, one horizontal) intersecting at exactly one point (3, 5).",
            "pages": [20, 21],
        },
        {
            "q": "Elimination method involves:",
            "options": [
                "A) Substituting values",
                "B) Making coefficients equal and adding/subtracting",
                "C) Graphing on coordinate axes",
                "D) Trial and error",
            ],
            "correct": "B",
            "explanation": "In elimination, multiply equations to make one variable's coefficients equal, then add/subtract to eliminate it.",
            "pages": [24, 25],
        },
    ]

    bank["Quadratic Equations"] = [
        {
            "q": "The standard form of a quadratic equation is:",
            "options": [
                "A) ax + b = 0",
                "B) ax² + bx + c = 0, a ≠ 0",
                "C) ax³ + bx² + cx + d = 0",
                "D) a/x + b = 0",
            ],
            "correct": "B",
            "explanation": "A quadratic equation is of the form ax² + bx + c = 0 where a, b, c are real numbers and a ≠ 0.",
            "pages": [28, 29],
        },
        {
            "q": "The discriminant of 2x² − 4x + 1 = 0 is:",
            "options": ["A) 8", "B) 12", "C) -8", "D) 0"],
            "correct": "A",
            "explanation": "D = b² − 4ac = (−4)² − 4(2)(1) = 16 − 8 = 8.",
            "pages": [32, 33],
        },
        {
            "q": "If discriminant > 0, the quadratic equation has:",
            "options": [
                "A) No real roots",
                "B) Two equal real roots",
                "C) Two distinct real roots",
                "D) Complex roots only",
            ],
            "correct": "C",
            "explanation": "D > 0 means the equation has two distinct (unequal) real roots.",
            "pages": [32, 33],
        },
        {
            "q": "Solve x² − 5x + 6 = 0:",
            "options": ["A) x = 1, 6", "B) x = 2, 3", "C) x = -2, -3", "D) x = -1, 6"],
            "correct": "B",
            "explanation": "x² − 5x + 6 = (x−2)(x−3) = 0. So x = 2 or x = 3.",
            "pages": [30, 31],
        },
        {
            "q": "The roots of x² + 4x + 4 = 0 are:",
            "options": ["A) −2 and −2", "B) 2 and 2", "C) 2 and −2", "D) 4 and 1"],
            "correct": "A",
            "explanation": "x² + 4x + 4 = (x+2)² = 0. Repeated root: x = −2.",
            "pages": [30, 31],
        },
        {
            "q": "Which method involves converting ax² + bx + c to a(x + d)² + e form?",
            "options": [
                "A) Factorisation",
                "B) Completing the square",
                "C) Quadratic formula",
                "D) Graphical method",
            ],
            "correct": "B",
            "explanation": "Completing the square transforms the equation to identify the vertex form and find roots.",
            "pages": [30, 31],
        },
        {
            "q": "The quadratic formula is:",
            "options": [
                "A) x = (-b ± √(b² − 4ac)) / 2a",
                "B) x = (-b ± √(b² + 4ac)) / 2a",
                "C) x = (b ± √(b² − 4ac)) / 2a",
                "D) x = -b / 2a",
            ],
            "correct": "A",
            "explanation": "The quadratic formula x = (−b ± √(b²−4ac))/2a gives the roots of any quadratic equation.",
            "pages": [32, 33],
        },
        {
            "q": "For x² − 3x + 2 = 0, sum of roots is:",
            "options": ["A) 2", "B) 3", "C) -3", "D) -2"],
            "correct": "B",
            "explanation": "Sum of roots = −b/a = −(−3)/1 = 3.",
            "pages": [28, 29],
        },
        {
            "q": "If D = 0 for a quadratic equation, the nature of roots is:",
            "options": [
                "A) Two distinct real roots",
                "B) Two equal real roots",
                "C) No real roots",
                "D) Three roots",
            ],
            "correct": "B",
            "explanation": "D = 0 means the equation has two equal (repeated) real roots: x = −b/2a.",
            "pages": [32, 33],
        },
        {
            "q": "The product of roots of 3x² − x − 2 = 0 is:",
            "options": ["A) 1/3", "B) -1/3", "C) -2/3", "D) 2/3"],
            "correct": "C",
            "explanation": "Product of roots = c/a = −2/3.",
            "pages": [28, 29],
        },
    ]

    bank["Arithmetic Progressions"] = [
        {
            "q": "In an AP, if a = 3 and d = 5, the 10th term is:",
            "options": ["A) 48", "B) 50", "C) 45", "D) 53"],
            "correct": "A",
            "explanation": "aₙ = a + (n−1)d = 3 + 9(5) = 3 + 45 = 48.",
            "pages": [34, 35],
        },
        {
            "q": "The sum of first n natural numbers is:",
            "options": ["A) n(n+1)", "B) n(n+1)/2", "C) n²", "D) 2n+1"],
            "correct": "B",
            "explanation": "Sum = n(n+1)/2. This is an AP with a=1, d=1.",
            "pages": [38, 39],
        },
        {
            "q": "If the 3rd term of an AP is 7 and the 7th term is 15, then d = ?",
            "options": ["A) 1", "B) 2", "C) 3", "D) 4"],
            "correct": "B",
            "explanation": "a₇ − a₃ = (7−3)d → 15 − 7 = 4d → d = 2.",
            "pages": [36, 37],
        },
        {
            "q": "The common difference of AP: 3, 7, 11, 15, ... is:",
            "options": ["A) 3", "B) 4", "C) 7", "D) 11"],
            "correct": "B",
            "explanation": "d = a₂ − a₁ = 7 − 3 = 4.",
            "pages": [34, 35],
        },
        {
            "q": "The sum of first 20 terms of AP: 1, 3, 5, 7, ... is:",
            "options": ["A) 400", "B) 200", "C) 380", "D) 420"],
            "correct": "A",
            "explanation": "Sₙ = n/2[2a + (n−1)d] = 20/2[2(1) + 19(2)] = 10[2+38] = 10×40 = 400.",
            "pages": [38, 39],
        },
        {
            "q": "Which of the following is NOT an AP?",
            "options": [
                "A) 1, 3, 5, 7, ...",
                "B) 2, 4, 8, 16, ...",
                "C) -5, -3, -1, 1, ...",
                "D) 10, 7, 4, 1, ...",
            ],
            "correct": "B",
            "explanation": "2, 4, 8, 16 is a GP (ratio = 2), not an AP (differences are 2, 4, 8 — not constant).",
            "pages": [34, 35],
        },
        {
            "q": "If in an AP, a = 2, d = 3, Sₙ = 65, then n = ?",
            "options": ["A) 5", "B) 6", "C) 7", "D) 8"],
            "correct": "B",
            "explanation": "65 = n/2[2(2)+(n−1)3] = n/2[4+3n−3] = n/2[3n+1]. Solving: 130 = 3n²+n → 3n²+n−130=0 → n=6.",
            "pages": [38, 39],
        },
        {
            "q": "The nth term of an AP is given by:",
            "options": [
                "A) aₙ = a + nd",
                "B) aₙ = a + (n−1)d",
                "C) aₙ = a − (n−1)d",
                "D) aₙ = an + d",
            ],
            "correct": "B",
            "explanation": "The nth term: aₙ = a + (n−1)d, where a is the first term and d is the common difference.",
            "pages": [34, 35],
        },
        {
            "q": "The 15th term of AP: 2, 5, 8, ... is:",
            "options": ["A) 42", "B) 44", "C) 46", "D) 47"],
            "correct": "B",
            "explanation": "a₁₅ = 2 + 14(3) = 2 + 42 = 44.",
            "pages": [34, 35],
        },
        {
            "q": "If the sum of first n terms of an AP is 3n² + 5n, the common difference is:",
            "options": ["A) 3", "B) 5", "C) 6", "D) 8"],
            "correct": "C",
            "explanation": "a₁ = S₁ = 8. a₂ = S₂ − S₁ = 22 − 8 = 14. d = 14 − 8 = 6.",
            "pages": [38, 39],
        },
    ]

    bank["Triangles"] = [
        {
            "q": "Two triangles are similar if their corresponding angles are:",
            "options": ["A) Equal", "B) Supplementary", "C) Complementary", "D) Right angles"],
            "correct": "A",
            "explanation": "Two triangles are similar if their corresponding angles are equal (AA, SAS, SSS similarity criteria).",
            "pages": [40, 41],
        },
        {
            "q": "BPT (Basic Proportionality Theorem) states: If a line is drawn parallel to one side of a triangle, it divides the other two sides:",
            "options": [
                "A) Equally",
                "B) In the same ratio",
                "C) Perpendicularly",
                "D) Into right triangles",
            ],
            "correct": "B",
            "explanation": "BPT (Thales' theorem): A line parallel to one side of a triangle divides the other two sides proportionally.",
            "pages": [40, 41],
        },
        {
            "q": "In a right triangle with sides 3, 4, and 5:",
            "options": ["A) 3² + 4² = 5²", "B) 3² + 5² = 4²", "C) 4² + 5² = 3²", "D) 3 + 4 = 5"],
            "correct": "A",
            "explanation": "9 + 16 = 25 → 3² + 4² = 5². This is a Pythagorean triplet.",
            "pages": [46, 47],
        },
        {
            "q": "The ratio of areas of two similar triangles is equal to:",
            "options": [
                "A) Ratio of their corresponding sides",
                "B) Square of the ratio of their corresponding sides",
                "C) Cube of the ratio of their corresponding sides",
                "D) Half the ratio of their corresponding sides",
            ],
            "correct": "B",
            "explanation": "If triangles are similar with side ratio k, then area ratio = k².",
            "pages": [44, 45],
        },
        {
            "q": "AAA criterion proves:",
            "options": ["A) Congruence", "B) Similarity", "C) Both", "D) Neither"],
            "correct": "B",
            "explanation": "AAA (all angles equal) proves similarity, not congruence (sides could be different lengths).",
            "pages": [42, 43],
        },
        {
            "q": "If △ABC ~ △DEF and AB/DE = 2/3, then area(△ABC)/area(△DEF) = ?",
            "options": ["A) 2/3", "B) 4/9", "C) 8/27", "D) 3/2"],
            "correct": "B",
            "explanation": "Area ratio = (side ratio)² = (2/3)² = 4/9.",
            "pages": [44, 45],
        },
        {
            "q": "In a triangle, the sum of any two sides is:",
            "options": [
                "A) Equal to the third side",
                "B) Less than the third side",
                "C) Greater than the third side",
                "D) None of these",
            ],
            "correct": "C",
            "explanation": "Triangle inequality: the sum of any two sides must be greater than the third side.",
            "pages": [40, 41],
        },
        {
            "q": "Converse of Pythagoras theorem states:",
            "options": [
                "A) In any triangle, c² = a² + b²",
                "B) If c² = a² + b², the triangle is right-angled",
                "C) All right triangles are similar",
                "D) Hypotenuse is the shortest side",
            ],
            "correct": "B",
            "explanation": "Converse: If the square of one side equals the sum of squares of other two sides, the triangle is right-angled.",
            "pages": [46, 47],
        },
        {
            "q": "SAS similarity criterion states: Two triangles are similar if:",
            "options": [
                "A) Two sides are equal",
                "B) One angle is equal and sides including it are proportional",
                "C) All sides are equal",
                "D) Two angles are equal",
            ],
            "correct": "B",
            "explanation": "SAS: If one angle of a triangle is equal to one angle of another and the including sides are proportional, they are similar.",
            "pages": [42, 43],
        },
        {
            "q": "A line drawn from the midpoint of one side parallel to another side bisects the third side. This is:",
            "options": [
                "A) BPT",
                "B) Converse of BPT",
                "C) Mid-point theorem",
                "D) Pythagoras theorem",
            ],
            "correct": "C",
            "explanation": "The mid-point theorem states that a line segment joining midpoints of two sides is parallel to and half the third side.",
            "pages": [40, 41],
        },
    ]

    bank["Coordinate Geometry"] = [
        {
            "q": "The distance between points (3, 4) and (0, 0) is:",
            "options": ["A) 5", "B) 7", "C) 25", "D) √7"],
            "correct": "A",
            "explanation": "d = √((3-0)² + (4-0)²) = √(9+16) = √25 = 5.",
            "pages": [48, 49],
        },
        {
            "q": "The midpoint of (2, 4) and (6, 8) is:",
            "options": ["A) (4, 6)", "B) (3, 5)", "C) (8, 12)", "D) (2, 2)"],
            "correct": "A",
            "explanation": "Midpoint = ((2+6)/2, (4+8)/2) = (4, 6).",
            "pages": [50, 51],
        },
        {
            "q": "The section formula for internal division in ratio m:n gives:",
            "options": [
                "A) ((mx₂+nx₁)/(m+n), (my₂+ny₁)/(m+n))",
                "B) ((mx₁+nx₂)/(m+n), (my₁+ny₂)/(m+n))",
                "C) ((x₁+x₂)/2, (y₁+y₂)/2)",
                "D) (mx₁−nx₂, my₁−ny₂)",
            ],
            "correct": "A",
            "explanation": "Section formula: P = ((mx₂+nx₁)/(m+n), (my₂+ny₁)/(m+n)) for internal division.",
            "pages": [52, 53],
        },
        {
            "q": "The area of a triangle with vertices (0,0), (4,0), and (0,3) is:",
            "options": ["A) 12", "B) 6", "C) 7", "D) 24"],
            "correct": "B",
            "explanation": "Area = ½|x₁(y₂−y₃) + x₂(y₃−y₁) + x₃(y₁−y₂)| = ½|0+12+0| = 6.",
            "pages": [54, 55],
        },
        {
            "q": "If three points are collinear, the area of the triangle formed is:",
            "options": ["A) 1", "B) Maximum", "C) 0", "D) Infinite"],
            "correct": "C",
            "explanation": "Collinear points lie on a line — no triangle is formed, so area = 0.",
            "pages": [54, 55],
        },
        {
            "q": "The distance between (1, 2) and (4, 6) is:",
            "options": ["A) 5", "B) 7", "C) 25", "D) 3"],
            "correct": "A",
            "explanation": "d = √((4−1)² + (6−2)²) = √(9+16) = √25 = 5.",
            "pages": [48, 49],
        },
        {
            "q": "The point which divides (1, 2) and (3, 4) in ratio 1:1 is:",
            "options": ["A) (1, 2)", "B) (2, 3)", "C) (3, 4)", "D) (4, 6)"],
            "correct": "B",
            "explanation": "1:1 internal division = midpoint = ((1+3)/2, (2+4)/2) = (2, 3).",
            "pages": [50, 51],
        },
        {
            "q": "The coordinates of the centroid of a triangle with vertices (x₁,y₁), (x₂,y₂), (x₃,y₃) are:",
            "options": [
                "A) ((x₁+x₂+x₃)/3, (y₁+y₂+y₃)/3)",
                "B) ((x₁+x₂)/2, (y₁+y₂)/2)",
                "C) (x₁x₂x₃, y₁y₂y₃)",
                "D) (x₁−x₂, y₁−y₂)",
            ],
            "correct": "A",
            "explanation": "Centroid divides each median in 2:1 ratio and equals the average of all three vertices' coordinates.",
            "pages": [52, 53],
        },
        {
            "q": "The distance of point (3, 4) from the origin is:",
            "options": ["A) 3", "B) 4", "C) 5", "D) 7"],
            "correct": "C",
            "explanation": "Distance from origin = √(3² + 4²) = √(9+16) = √25 = 5.",
            "pages": [48, 49],
        },
        {
            "q": "The point equidistant from A(−2, 0) and B(2, 0) on the y-axis is:",
            "options": ["A) (0, 0)", "B) (0, 2)", "C) (2, 0)", "D) Any point on y-axis"],
            "correct": "D",
            "explanation": "Since A and B are symmetric about y-axis, every point on the y-axis is equidistant from both.",
            "pages": [48, 49],
        },
    ]

    bank["Introduction to Trigonometry"] = [
        {
            "q": "sin 30° = ?",
            "options": ["A) 1/2", "B) 1/√2", "C) √3/2", "D) 1"],
            "correct": "A",
            "explanation": "sin 30° = 1/2 is a standard trigonometric value.",
            "pages": [56, 57],
        },
        {
            "q": "tan 45° = ?",
            "options": ["A) 0", "B) 1", "C) √3", "D) 1/√3"],
            "correct": "B",
            "explanation": "tan 45° = sin 45°/cos 45° = (1/√2)/(1/√2) = 1.",
            "pages": [56, 57],
        },
        {
            "q": "sin²θ + cos²θ = ?",
            "options": ["A) 0", "B) 1", "C) 2", "D) tan²θ"],
            "correct": "B",
            "explanation": "This is the fundamental Pythagorean identity: sin²θ + cos²θ = 1.",
            "pages": [60, 61],
        },
        {
            "q": "cos 0° = ?",
            "options": ["A) 0", "B) 1/2", "C) 1", "D) √3/2"],
            "correct": "C",
            "explanation": "cos 0° = 1 is a standard value.",
            "pages": [56, 57],
        },
        {
            "q": "sin(90° − θ) = ?",
            "options": ["A) sin θ", "B) cos θ", "C) tan θ", "D) sec θ"],
            "correct": "B",
            "explanation": "sin(90° − θ) = cos θ. This is the complementary angle identity.",
            "pages": [58, 59],
        },
        {
            "q": "If tan θ = 3/4, then sin θ = ?",
            "options": ["A) 3/5", "B) 4/5", "C) 3/4", "D) 5/3"],
            "correct": "A",
            "explanation": "If tan θ = 3/4, then in right triangle: opposite=3, adjacent=4, hypotenuse=5. sin θ = 3/5.",
            "pages": [56, 57],
        },
        {
            "q": "sec θ is the reciprocal of:",
            "options": ["A) sin θ", "B) cos θ", "C) tan θ", "D) cot θ"],
            "correct": "B",
            "explanation": "sec θ = 1/cos θ. Similarly, cosec θ = 1/sin θ and cot θ = 1/tan θ.",
            "pages": [60, 61],
        },
        {
            "q": "The value of sin 60° is:",
            "options": ["A) 1/2", "B) √3/2", "C) 1/√2", "D) √3"],
            "correct": "B",
            "explanation": "sin 60° = √3/2 ≈ 0.866.",
            "pages": [56, 57],
        },
        {
            "q": "1 + tan²θ = ?",
            "options": ["A) sec²θ", "B) cosec²θ", "C) sin²θ", "D) cos²θ"],
            "correct": "A",
            "explanation": "This is the second Pythagorean identity: 1 + tan²θ = sec²θ.",
            "pages": [60, 61],
        },
        {
            "q": "cos 90° = ?",
            "options": ["A) 1", "B) 0", "C) −1", "D) 1/2"],
            "correct": "B",
            "explanation": "cos 90° = 0. At 90°, the adjacent side has zero length.",
            "pages": [56, 57],
        },
    ]

    # Remaining Class 10 Mathematics Chapters
    bank["Some Applications of Trigonometry"] = [
        {
            "q": "A tower stands vertically on the ground. From a point 15 m away from the foot, the angle of elevation of top is 60°. The height of tower is:",
            "options": ["A) 15√3 m", "B) 15/√3 m", "C) 30 m", "D) 15 m"],
            "correct": "A",
            "explanation": "tan 60° = h / 15 → √3 = h / 15 → h = 15√3 m.",
            "pages": [64, 65],
        },
        {
            "q": "The angle of elevation of the sun when the shadow of a pole is √3 times its height is:",
            "options": ["A) 30°", "B) 45°", "C) 60°", "D) 90°"],
            "correct": "A",
            "explanation": "tan θ = h / (h√3) = 1/√3 → θ = 30°.",
            "pages": [64, 65],
        },
        {
            "q": "The line drawn from the eye of an observer to the point in the object viewed is called:",
            "options": [
                "A) Horizontal line",
                "B) Line of sight",
                "C) Normal line",
                "D) Tangent line",
            ],
            "correct": "B",
            "explanation": "The line of sight is the straight line drawn from the observer's eye to the viewed object.",
            "pages": [62, 63],
        },
        {
            "q": "Angle of depression is formed when the object is:",
            "options": [
                "A) Above the horizontal level",
                "B) Below the horizontal level",
                "C) At the horizontal level",
                "D) At infinity",
            ],
            "correct": "B",
            "explanation": "Angle of depression is between the horizontal line and line of sight when viewing downward.",
            "pages": [62, 63],
        },
        {
            "q": "A kite is flying at a height of 60 m. String is inclined at 60° to the horizontal. Length of string is:",
            "options": ["A) 40√3 m", "B) 30√3 m", "C) 120 m", "D) 60√3 m"],
            "correct": "A",
            "explanation": "sin 60° = 60 / L → √3/2 = 60 / L → L = 120 / √3 = 40√3 m.",
            "pages": [66, 67],
        },
        {
            "q": "If the angle of elevation of a cloud from a point h metres above a lake is θ and depression of its reflection is φ, then height of cloud depends on:",
            "options": ["A) tan θ and tan φ", "B) sin θ only", "C) cos φ only", "D) h only"],
            "correct": "A",
            "explanation": "Height of cloud above lake H = h(tan φ + tan θ) / (tan φ − tan θ).",
            "pages": [66, 67],
        },
        {
            "q": "From the top of a 7 m high building, angle of elevation of top of cable tower is 60° and depression of foot is 45°. Height of tower is:",
            "options": ["A) 7(√3 + 1) m", "B) 7(√3 − 1) m", "C) 14√3 m", "D) 21 m"],
            "correct": "A",
            "explanation": "Distance d = 7 / tan 45° = 7 m. Tower height = 7 + 7 tan 60° = 7(1 + √3) m.",
            "pages": [66, 67],
        },
        {
            "q": "A 1.5 m tall boy stands at some distance from a 30 m tall building. If angle increases from 30° to 60° as he walks toward it, distance walked is:",
            "options": ["A) 19√3 m", "B) 28.5√3 m", "C) 57√3 m", "D) 10√3 m"],
            "correct": "A",
            "explanation": "Height above eye level = 28.5 m. d = 28.5(cot 30° − cot 60°) = 28.5(√3 − 1/√3) = 19√3 m.",
            "pages": [66, 67],
        },
        {
            "q": "When observer moves away from the foot of a tower, the angle of elevation:",
            "options": ["A) Increases", "B) Decreases", "C) Remains constant", "D) Becomes 90°"],
            "correct": "B",
            "explanation": "As distance from base increases, the angle of elevation decreases (tan θ = h/d).",
            "pages": [62, 63],
        },
        {
            "q": "The shadow of a vertical tower on level ground increases by 10 m when sun's altitude changes from 45° to 30°. Height of tower is:",
            "options": ["A) 5(√3 + 1) m", "B) 5(√3 − 1) m", "C) 10(√3 + 1) m", "D) 10(√3 − 1) m"],
            "correct": "A",
            "explanation": "h cot 30° − h cot 45° = 10 → h(√3 − 1) = 10 → h = 10 / (√3 − 1) = 5(√3 + 1) m.",
            "pages": [66, 67],
        },
    ]

    bank["Circles"] = [
        {
            "q": "The tangent at any point of a circle is perpendicular to the:",
            "options": [
                "A) Chord",
                "B) Radius through the point of contact",
                "C) Diameter parallel to it",
                "D) Secant",
            ],
            "correct": "B",
            "explanation": "Theorem 10.1: The tangent at any point of a circle is perpendicular to the radius through the point of contact.",
            "pages": [70, 71],
        },
        {
            "q": "From an external point P, tangents PA and PB are drawn to a circle. Then:",
            "options": ["A) PA > PB", "B) PA < PB", "C) PA = PB", "D) PA = 2PB"],
            "correct": "C",
            "explanation": "Theorem 10.2: The lengths of tangents drawn from an external point to a circle are equal.",
            "pages": [72, 73],
        },
        {
            "q": "How many tangents can be drawn to a circle from a point inside the circle?",
            "options": ["A) 0", "B) 1", "C) 2", "D) Infinite"],
            "correct": "A",
            "explanation": "No tangent can be drawn from a point inside a circle because every line through it will intersect the circle twice (secant).",
            "pages": [70, 71],
        },
        {
            "q": "The number of parallel tangents a circle can have at most is:",
            "options": ["A) 1", "B) 2", "C) 4", "D) Infinite pairs"],
            "correct": "B",
            "explanation": "A circle can have at most two parallel tangents at the endpoints of a diameter.",
            "pages": [70, 71],
        },
        {
            "q": "If PA and PB are tangents from P to circle with centre O inclined at 80°, then ∠POA = ?",
            "options": ["A) 50°", "B) 60°", "C) 70°", "D) 80°"],
            "correct": "A",
            "explanation": "∠AOB = 180° − 80° = 100°. Since OP bisects ∠AOB, ∠POA = 100° / 2 = 50°.",
            "pages": [72, 73],
        },
        {
            "q": "A tangent intersects a circle at:",
            "options": ["A) Exactly one point", "B) Two points", "C) Three points", "D) No points"],
            "correct": "A",
            "explanation": "By definition, a tangent is a straight line that touches the circle at exactly one distinct point.",
            "pages": [68, 69],
        },
        {
            "q": "If radius is 5 cm and distance of external point from centre is 13 cm, tangent length is:",
            "options": ["A) 12 cm", "B) 10 cm", "C) 8 cm", "D) 18 cm"],
            "correct": "A",
            "explanation": "By Pythagoras: L = √(13² − 5²) = √(169 − 25) = √144 = 12 cm.",
            "pages": [72, 73],
        },
        {
            "q": "A quadrilateral ABCD circumscribes a circle. Then AB + CD = ?",
            "options": ["A) AD + BC", "B) AC + BD", "C) AB + BC", "D) 2(AD + BC)"],
            "correct": "A",
            "explanation": "Lengths of tangents from each vertex are equal, proving AB + CD = AD + BC.",
            "pages": [74, 75],
        },
        {
            "q": "The common point of a tangent to a circle and the circle is called:",
            "options": ["A) Point of contact", "B) Centre", "C) Chord", "D) Origin"],
            "correct": "A",
            "explanation": "The single point where the tangent touches the circle is called the point of contact.",
            "pages": [68, 69],
        },
        {
            "q": "Two concentric circles have radii 5 cm and 3 cm. Length of chord of larger circle touching smaller is:",
            "options": ["A) 8 cm", "B) 6 cm", "C) 4 cm", "D) 10 cm"],
            "correct": "A",
            "explanation": "Half chord = √(5² − 3²) = 4 cm. Full chord = 2 × 4 = 8 cm.",
            "pages": [72, 73],
        },
    ]

    bank["Areas Related to Circles"] = [
        {
            "q": "Area of a sector of angle θ of a circle with radius r is:",
            "options": [
                "A) (θ/360°) × πr²",
                "B) (θ/180°) × πr²",
                "C) (θ/360°) × 2πr",
                "D) (θ/720°) × 2πr²",
            ],
            "correct": "A",
            "explanation": "Area of sector = (θ/360°) × πr².",
            "pages": [76, 77],
        },
        {
            "q": "Length of an arc of a sector of angle θ is:",
            "options": [
                "A) (θ/360°) × 2πr",
                "B) (θ/180°) × πr²",
                "C) (θ/360°) × πr²",
                "D) (θ/720°) × 2πr",
            ],
            "correct": "A",
            "explanation": "Arc length l = (θ/360°) × 2πr.",
            "pages": [76, 77],
        },
        {
            "q": "If the perimeter and area of a circle are numerically equal, the radius is:",
            "options": ["A) 2 units", "B) π units", "C) 4 units", "D) 7 units"],
            "correct": "A",
            "explanation": "2πr = πr² → r = 2 units.",
            "pages": [78, 79],
        },
        {
            "q": "Area of a segment of a circle is calculated by:",
            "options": [
                "A) Area of sector − Area of corresponding triangle",
                "B) Area of sector + Area of triangle",
                "C) Area of sector / 2",
                "D) Area of circle − Area of sector",
            ],
            "correct": "A",
            "explanation": "Area of minor segment = Area of sector OAB − Area of △OAB.",
            "pages": [80, 81],
        },
        {
            "q": "The area of a circle that can be inscribed in a square of side 6 cm is:",
            "options": ["A) 9π cm²", "B) 36π cm²", "C) 18π cm²", "D) 12π cm²"],
            "correct": "A",
            "explanation": "Diameter of circle = side = 6 cm → r = 3 cm. Area = π(3)² = 9π cm².",
            "pages": [82, 83],
        },
        {
            "q": "If the circumference of a circle increases from 4π to 8π, its area:",
            "options": ["A) Halves", "B) Doubles", "C) Triples", "D) Quadruples"],
            "correct": "D",
            "explanation": "Radius doubles from 2 to 4. Area increases by factor of 2² = 4 (quadruples).",
            "pages": [78, 79],
        },
        {
            "q": "Area of a quadrant of a circle of radius 14 cm is (use π = 22/7):",
            "options": ["A) 154 cm²", "B) 77 cm²", "C) 308 cm²", "D) 616 cm²"],
            "correct": "A",
            "explanation": "Area = ¼ × (22/7) × 14 × 14 = ¼ × 616 = 154 cm².",
            "pages": [76, 77],
        },
        {
            "q": "A racetrack is in the form of a ring whose inner and outer circumferences are 44 m and 88 m. Width is:",
            "options": ["A) 7 m", "B) 14 m", "C) 21 m", "D) 3.5 m"],
            "correct": "A",
            "explanation": "R = 88 / 2π = 14 m; r = 44 / 2π = 7 m. Width = R − r = 14 − 7 = 7 m.",
            "pages": [82, 83],
        },
        {
            "q": "The minute hand of a clock is 14 cm long. Area swept by it in 5 minutes is:",
            "options": ["A) 51.33 cm²", "B) 154 cm²", "C) 25.67 cm²", "D) 77 cm²"],
            "correct": "A",
            "explanation": "In 5 min, angle θ = (360°/60) × 5 = 30°. Area = (30/360) × (22/7) × 14² = 1/12 × 616 = 51.33 cm².",
            "pages": [76, 77],
        },
        {
            "q": "Area of the largest triangle inscribed in a semicircle of radius r is:",
            "options": ["A) r²", "B) ½r²", "C) 2r²", "D) √2 r²"],
            "correct": "A",
            "explanation": "Base = 2r, maximum height = r. Area = ½ × 2r × r = r².",
            "pages": [80, 81],
        },
    ]

    bank["Surface Areas and Volumes"] = [
        {
            "q": "A solid cylinder of radius r and height h is melted and recast into spheres of radius r. Number of spheres is:",
            "options": ["A) 3h / 4r", "B) h / r", "C) 4h / 3r", "D) 3r / 4h"],
            "correct": "A",
            "explanation": "Volume of cylinder = πr²h. Volume of sphere = 4/3 πr³. n = (πr²h) / (4/3 πr³) = 3h / 4r.",
            "pages": [86, 87],
        },
        {
            "q": "Total surface area of a solid hemisphere of radius r is:",
            "options": ["A) 2πr²", "B) 3πr²", "C) 4πr²", "D) ⅔πr²"],
            "correct": "B",
            "explanation": "Curved surface area (2πr²) + flat circular base (πr²) = 3πr².",
            "pages": [84, 85],
        },
        {
            "q": "The slant height of a cone with radius 3 cm and height 4 cm is:",
            "options": ["A) 5 cm", "B) 7 cm", "C) 12 cm", "D) 25 cm"],
            "correct": "A",
            "explanation": "l = √(r² + h²) = √(3² + 4²) = √25 = 5 cm.",
            "pages": [84, 85],
        },
        {
            "q": "Curved surface area of a frustum of cone with radii r₁, r₂ and slant height l is:",
            "options": ["A) π(r₁ + r₂)l", "B) π(r₁ − r₂)l", "C) 2π(r₁ + r₂)l", "D) π(r₁² + r₂²)l"],
            "correct": "A",
            "explanation": "CSA of frustum = π(r₁ + r₂)l.",
            "pages": [90, 91],
        },
        {
            "q": "Two cubes each of volume 64 cm³ are joined end to end. Total surface area of resulting cuboid is:",
            "options": ["A) 128 cm²", "B) 160 cm²", "C) 192 cm²", "D) 256 cm²"],
            "correct": "B",
            "explanation": "Side of cube = 4 cm. Cuboid dimensions: 8 × 4 × 4. TSA = 2(32 + 16 + 32) = 2(80) = 160 cm².",
            "pages": [86, 87],
        },
        {
            "q": "Volume of a cone is what fraction of volume of cylinder of same radius and height?",
            "options": ["A) 1/2", "B) 1/3", "C) 2/3", "D) 1/4"],
            "correct": "B",
            "explanation": "V_cone = ⅓πr²h, which is exactly one-third of V_cylinder = πr²h.",
            "pages": [84, 85],
        },
        {
            "q": "If radius of a sphere is doubled, its volume becomes:",
            "options": ["A) 2 times", "B) 4 times", "C) 8 times", "D) 16 times"],
            "correct": "C",
            "explanation": "Volume is proportional to r³. When r → 2r, volume becomes 2³ = 8 times.",
            "pages": [86, 87],
        },
        {
            "q": "The ratio of total surface area to lateral surface area of a cylinder of radius 20 cm and height 60 cm is:",
            "options": ["A) 4:3", "B) 3:4", "C) 2:3", "D) 3:2"],
            "correct": "A",
            "explanation": "TSA / CSA = 2πr(r+h) / 2πrh = (r+h)/h = (20+60)/60 = 80/60 = 4/3.",
            "pages": [84, 85],
        },
        {
            "q": "A metallic sphere of radius 10.5 cm is melted and recast into small cones of radius 3.5 cm and height 3 cm. Number of cones is:",
            "options": ["A) 126", "B) 130", "C) 112", "D) 140"],
            "correct": "A",
            "explanation": "n = (4/3 π × 10.5³) / (⅓ π × 3.5² × 3) = (4 × 1157.625) / 36.75 = 126.",
            "pages": [88, 89],
        },
        {
            "q": "Diagonal of a cuboid of dimensions l, b, h is:",
            "options": [
                "A) √(l² + b² + h²)",
                "B) l + b + h",
                "C) √(lb + bh + hl)",
                "D) 2(l + b + h)",
            ],
            "correct": "A",
            "explanation": "Space diagonal of a cuboid d = √(l² + b² + h²).",
            "pages": [84, 85],
        },
    ]

    bank["Statistics"] = [
        {
            "q": "The empirical relationship between mean, median and mode is:",
            "options": [
                "A) Mode = 3 Median − 2 Mean",
                "B) Mode = 2 Median − 3 Mean",
                "C) Median = 3 Mode − 2 Mean",
                "D) Mean = 3 Median − 2 Mode",
            ],
            "correct": "A",
            "explanation": "Empirical formula: Mode = 3 Median − 2 Mean.",
            "pages": [92, 93],
        },
        {
            "q": "The class mark of the class interval 10–25 is:",
            "options": ["A) 17.5", "B) 15", "C) 20", "D) 35"],
            "correct": "A",
            "explanation": "Class mark = (Upper limit + Lower limit) / 2 = (25 + 10) / 2 = 17.5.",
            "pages": [92, 93],
        },
        {
            "q": "For grouped data, mode is given by l + [(f₁ − f₀) / (2f₁ − f₀ − f₂)] × h. Here f₁ is:",
            "options": [
                "A) Frequency of modal class",
                "B) Frequency of class preceding modal class",
                "C) Frequency of class succeeding modal class",
                "D) Cumulative frequency",
            ],
            "correct": "A",
            "explanation": "f₁ is the frequency of the modal class; f₀ is preceding, f₂ is succeeding frequency.",
            "pages": [96, 97],
        },
        {
            "q": "The intersection point of 'less than' and 'more than' ogives gives the:",
            "options": ["A) Mean", "B) Median", "C) Mode", "D) Range"],
            "correct": "B",
            "explanation": "The abscissa (x-coordinate) of the intersection point of less than and more than ogives is the median.",
            "pages": [100, 101],
        },
        {
            "q": "If mean = 20 and median = 22, mode is:",
            "options": ["A) 26", "B) 24", "C) 21", "D) 18"],
            "correct": "A",
            "explanation": "Mode = 3(Median) − 2(Mean) = 3(22) − 2(20) = 66 − 40 = 26.",
            "pages": [96, 97],
        },
        {
            "q": "Assumed mean method simplifies calculation of:",
            "options": ["A) Mean", "B) Median", "C) Mode", "D) Variance"],
            "correct": "A",
            "explanation": "Assumed mean method: x̄ = a + (∑fᵢdᵢ / ∑fᵢ) simplifies arithmetic for calculating the mean.",
            "pages": [94, 95],
        },
        {
            "q": "Cumulative frequency is required for calculating:",
            "options": ["A) Median", "B) Mean", "C) Mode", "D) Standard deviation"],
            "correct": "A",
            "explanation": "Cumulative frequency table is essential for identifying the median class and computing the median.",
            "pages": [98, 99],
        },
        {
            "q": "The algebraic sum of deviations of observations from their mean is:",
            "options": ["A) 0", "B) 1", "C) Positive", "D) Negative"],
            "correct": "A",
            "explanation": "∑(xᵢ − x̄) = ∑xᵢ − n x̄ = n x̄ − n x̄ = 0. Always zero.",
            "pages": [92, 93],
        },
        {
            "q": "If each observation in a data set is increased by 5, the mean:",
            "options": [
                "A) Increases by 5",
                "B) Remains same",
                "C) Is multiplied by 5",
                "D) Decreases by 5",
            ],
            "correct": "A",
            "explanation": "Adding a constant k to all observations increases the mean by k.",
            "pages": [92, 93],
        },
        {
            "q": "The modal class is the class interval having:",
            "options": [
                "A) Maximum frequency",
                "B) Minimum frequency",
                "C) Highest cumulative frequency",
                "D) Lowest class mark",
            ],
            "correct": "A",
            "explanation": "The modal class is the interval with the highest frequency in a grouped frequency distribution.",
            "pages": [96, 97],
        },
    ]

    bank["Probability"] = [
        {
            "q": "The probability of an impossible event is:",
            "options": ["A) 0", "B) 1", "C) 0.5", "D) −1"],
            "correct": "A",
            "explanation": "An impossible event cannot happen, so P(E) = 0.",
            "pages": [102, 103],
        },
        {
            "q": "For any event E, P(E) + P(not E) = ?",
            "options": ["A) 1", "B) 0", "C) 0.5", "D) 2"],
            "correct": "A",
            "explanation": "The sum of probabilities of complementary events is always 1.",
            "pages": [102, 103],
        },
        {
            "q": "A card is drawn from a well-shuffled deck of 52 cards. Probability of getting a King is:",
            "options": ["A) 1/13", "B) 1/52", "C) 4/13", "D) 1/4"],
            "correct": "A",
            "explanation": "There are 4 Kings in 52 cards. P = 4/52 = 1/13.",
            "pages": [104, 105],
        },
        {
            "q": "Which of the following cannot be the probability of an event?",
            "options": ["A) 2/3", "B) −1.5", "C) 15%", "D) 0.7"],
            "correct": "B",
            "explanation": "Probability of any event must lie in the range [0, 1]. It cannot be negative.",
            "pages": [102, 103],
        },
        {
            "q": "Two dice are thrown simultaneously. Probability of getting a sum of 7 is:",
            "options": ["A) 1/6", "B) 1/12", "C) 7/36", "D) 5/36"],
            "correct": "A",
            "explanation": "Favourable outcomes: (1,6),(2,5),(3,4),(4,3),(5,2),(6,1) = 6. Total = 36. P = 6/36 = 1/6.",
            "pages": [106, 107],
        },
        {
            "q": "A bag contains 3 red and 5 black balls. Probability of drawing a red ball is:",
            "options": ["A) 3/8", "B) 5/8", "C) 3/5", "D) 1/8"],
            "correct": "A",
            "explanation": "Total balls = 8. Favourable = 3. P = 3/8.",
            "pages": [104, 105],
        },
        {
            "q": "Probability of getting a prime number on throwing a single die is:",
            "options": ["A) 1/2", "B) 1/3", "C) 2/3", "D) 1/6"],
            "correct": "A",
            "explanation": "Prime numbers on a die: 2, 3, 5 (3 numbers). P = 3/6 = 1/2.",
            "pages": [104, 105],
        },
        {
            "q": "Probability of a sure (certain) event is:",
            "options": ["A) 1", "B) 0", "C) 0.5", "D) Infinite"],
            "correct": "A",
            "explanation": "A certain event will definitely happen, so P = 1.",
            "pages": [102, 103],
        },
        {
            "q": "A leap year has 53 Sundays with probability:",
            "options": ["A) 2/7", "B) 1/7", "C) 53/366", "D) 5/7"],
            "correct": "A",
            "explanation": "Leap year has 366 days = 52 weeks + 2 days. 2 extra days can be (Sat,Sun) or (Sun,Mon) → 2/7.",
            "pages": [106, 107],
        },
        {
            "q": "In a simultaneous toss of two coins, probability of getting at least one head is:",
            "options": ["A) 3/4", "B) 1/4", "C) 1/2", "D) 1"],
            "correct": "A",
            "explanation": "Outcomes: HH, HT, TH, TT. At least one head: HH, HT, TH (3 outcomes). P = 3/4.",
            "pages": [104, 105],
        },
    ]

    # ===================== CLASS 9 MATHEMATICS CHAPTERS =====================
    bank["Orienting Yourself: The Use of Coordinates"] = [
        {
            "q": "The x-coordinate of a point on the y-axis is always:",
            "options": ["A) 0", "B) 1", "C) Positive", "D) Negative"],
            "correct": "A",
            "explanation": "Any point on the y-axis has x-coordinate = 0, written as (0, y).",
            "pages": [2, 3],
        },
        {
            "q": "The point (−3, 4) lies in which quadrant?",
            "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
            "correct": "B",
            "explanation": "In the second quadrant: x is negative, y is positive.",
            "pages": [4, 5],
        },
        {
            "q": "The origin has coordinates:",
            "options": ["A) (1, 1)", "B) (0, 1)", "C) (0, 0)", "D) (1, 0)"],
            "correct": "C",
            "explanation": "The origin is the intersection of x and y axes at (0, 0).",
            "pages": [2, 3],
        },
        {
            "q": "The y-coordinate is also called:",
            "options": ["A) Abscissa", "B) Ordinate", "C) Origin", "D) Axis"],
            "correct": "B",
            "explanation": "The x-coordinate is called abscissa and the y-coordinate is called ordinate.",
            "pages": [2, 3],
        },
        {
            "q": "The point (5, −2) lies in which quadrant?",
            "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
            "correct": "D",
            "explanation": "Fourth quadrant: x is positive, y is negative.",
            "pages": [4, 5],
        },
        {
            "q": "Which axis is horizontal?",
            "options": ["A) x-axis", "B) y-axis", "C) z-axis", "D) None"],
            "correct": "A",
            "explanation": "The x-axis is horizontal and the y-axis is vertical in the Cartesian plane.",
            "pages": [2, 3],
        },
        {
            "q": "If a point has both coordinates positive, it lies in:",
            "options": ["A) Q1", "B) Q2", "C) Q3", "D) Q4"],
            "correct": "A",
            "explanation": "First quadrant (Q1): both x and y coordinates are positive.",
            "pages": [4, 5],
        },
        {
            "q": "Mirror image of (3, 5) in x-axis is:",
            "options": ["A) (3, −5)", "B) (−3, 5)", "C) (−3, −5)", "D) (5, 3)"],
            "correct": "A",
            "explanation": "Reflection in x-axis: y changes sign. (3, 5) → (3, −5).",
            "pages": [6, 7],
        },
        {
            "q": "The distance of (4, 3) from x-axis is:",
            "options": ["A) 4", "B) 3", "C) 5", "D) 7"],
            "correct": "B",
            "explanation": "Distance from x-axis = |y-coordinate| = |3| = 3.",
            "pages": [4, 5],
        },
        {
            "q": "Which quadrant has (−, −) coordinates?",
            "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
            "correct": "C",
            "explanation": "Third quadrant: both x and y are negative.",
            "pages": [4, 5],
        },
    ]

    bank["Introduction to Linear Polynomials"] = [
        {
            "q": "The degree of a linear polynomial is:",
            "options": ["A) 0", "B) 1", "C) 2", "D) 3"],
            "correct": "B",
            "explanation": "A linear polynomial has degree 1, e.g., 2x + 3.",
            "pages": [10, 11],
        },
        {
            "q": "The zero of p(x) = 3x − 6 is:",
            "options": ["A) 3", "B) 6", "C) 2", "D) −2"],
            "correct": "C",
            "explanation": "3x − 6 = 0 → x = 2.",
            "pages": [12, 13],
        },
        {
            "q": "A polynomial with one term is called:",
            "options": ["A) Binomial", "B) Trinomial", "C) Monomial", "D) Constant"],
            "correct": "C",
            "explanation": "Monomial has one term, binomial has two, trinomial has three.",
            "pages": [10, 11],
        },
        {
            "q": "The value of p(x) = x² − 3x + 2 at x = 1 is:",
            "options": ["A) 0", "B) 1", "C) 2", "D) −1"],
            "correct": "A",
            "explanation": "p(1) = 1 − 3 + 2 = 0. So x = 1 is a zero of this polynomial.",
            "pages": [14, 15],
        },
        {
            "q": "If p(a) = 0, then x = a is called:",
            "options": ["A) Coefficient", "B) Zero of the polynomial", "C) Degree", "D) Variable"],
            "correct": "B",
            "explanation": "A zero (or root) of p(x) is a value 'a' such that p(a) = 0.",
            "pages": [12, 13],
        },
        {
            "q": "The remainder when x³ + 1 is divided by x + 1 is:",
            "options": ["A) 0", "B) 1", "C) 2", "D) −1"],
            "correct": "A",
            "explanation": "By Remainder Theorem: p(−1) = (−1)³ + 1 = −1 + 1 = 0.",
            "pages": [16, 17],
        },
        {
            "q": "A constant polynomial has degree:",
            "options": ["A) 1", "B) 0", "C) 2", "D) Undefined for zero polynomial"],
            "correct": "B",
            "explanation": "A non-zero constant (like 7) is a polynomial of degree 0. The zero polynomial has undefined degree.",
            "pages": [10, 11],
        },
        {
            "q": "x² + 5x + 6 = (x + 2)(x + 3) is an example of:",
            "options": ["A) Addition", "B) Factorisation", "C) Subtraction", "D) Differentiation"],
            "correct": "B",
            "explanation": "Expressing a polynomial as a product of its factors is called factorisation.",
            "pages": [14, 15],
        },
        {
            "q": "The coefficient of x² in 4x³ − 3x² + 2x − 1 is:",
            "options": ["A) 4", "B) −3", "C) 2", "D) −1"],
            "correct": "B",
            "explanation": "The coefficient of x² is −3 (the number multiplying x²).",
            "pages": [10, 11],
        },
        {
            "q": "Every linear polynomial has exactly ___ zero(s).",
            "options": ["A) 0", "B) 1", "C) 2", "D) 3"],
            "correct": "B",
            "explanation": "A linear polynomial ax + b = 0 has exactly one zero: x = −b/a.",
            "pages": [12, 13],
        },
    ]

    bank["The World of Numbers"] = [
        {
            "q": "Rational numbers can be expressed as:",
            "options": [
                "A) p/q where q ≠ 0",
                "B) Only whole numbers",
                "C) Only integers",
                "D) Decimals that never terminate or repeat",
            ],
            "correct": "A",
            "explanation": "Rational numbers are of the form p/q where p, q are integers and q ≠ 0.",
            "pages": [1, 2],
        },
        {
            "q": "√2 is an example of:",
            "options": [
                "A) Rational number",
                "B) Irrational number",
                "C) Integer",
                "D) Whole number",
            ],
            "correct": "B",
            "explanation": "√2 cannot be expressed as p/q — it is irrational.",
            "pages": [3, 4],
        },
        {
            "q": "Between any two rational numbers, there are:",
            "options": [
                "A) No numbers",
                "B) Exactly one rational",
                "C) Infinitely many rationals",
                "D) Only integers",
            ],
            "correct": "C",
            "explanation": "Between any two rationals, there exist infinitely many rational numbers (dense property).",
            "pages": [5, 6],
        },
        {
            "q": "π is:",
            "options": ["A) Rational", "B) Irrational", "C) An integer", "D) A natural number"],
            "correct": "B",
            "explanation": "π = 3.14159... is a non-terminating, non-repeating decimal — irrational.",
            "pages": [3, 4],
        },
        {
            "q": "The decimal expansion of 1/3 is:",
            "options": [
                "A) Terminating",
                "B) Non-terminating repeating",
                "C) Non-terminating non-repeating",
                "D) An integer",
            ],
            "correct": "B",
            "explanation": "1/3 = 0.333... is non-terminating but repeating — hence rational.",
            "pages": [5, 6],
        },
        {
            "q": "Rationalising the denominator of 1/√2 gives:",
            "options": ["A) √2/2", "B) 2/√2", "C) 1/2", "D) √2"],
            "correct": "A",
            "explanation": "1/√2 × √2/√2 = √2/2.",
            "pages": [7, 8],
        },
        {
            "q": "a^m × a^n = ?",
            "options": ["A) a^(m+n)", "B) a^(mn)", "C) a^(m−n)", "D) (2a)^(m+n)"],
            "correct": "A",
            "explanation": "When multiplying powers with same base, add exponents: a^m × a^n = a^(m+n).",
            "pages": [7, 8],
        },
        {
            "q": "(a^m)^n = ?",
            "options": ["A) a^(m+n)", "B) a^(mn)", "C) a^(m−n)", "D) a^m + a^n"],
            "correct": "B",
            "explanation": "Power of a power: multiply exponents: (a^m)^n = a^(mn).",
            "pages": [7, 8],
        },
        {
            "q": "The sum of a rational and an irrational number is:",
            "options": [
                "A) Always rational",
                "B) Always irrational",
                "C) Sometimes rational",
                "D) Zero",
            ],
            "correct": "B",
            "explanation": "Rational + Irrational = Irrational (always).",
            "pages": [3, 4],
        },
        {
            "q": "Which of these is rational?",
            "options": ["A) √3", "B) √4", "C) √5", "D) √7"],
            "correct": "B",
            "explanation": "√4 = 2, which is rational. The others are irrational.",
            "pages": [3, 4],
        },
    ]

    bank["Exploring Algebraic Identities"] = [
        {
            "q": "(a + b)² = ?",
            "options": ["A) a² + 2ab + b²", "B) a² + b²", "C) a² − 2ab + b²", "D) a² + ab + b²"],
            "correct": "A",
            "explanation": "Standard identity: (a + b)² = a² + 2ab + b².",
            "pages": [20, 21],
        },
        {
            "q": "(a − b)(a + b) = ?",
            "options": ["A) a² − b²", "B) a² + b²", "C) (a − b)²", "D) a² − 2ab + b²"],
            "correct": "A",
            "explanation": "Difference of squares identity: (a − b)(a + b) = a² − b².",
            "pages": [20, 21],
        },
        {
            "q": "Evaluate 105 × 106 using identity (x + a)(x + b):",
            "options": ["A) 11130", "B) 11030", "C) 11230", "D) 11120"],
            "correct": "A",
            "explanation": "(100 + 5)(100 + 6) = 100² + (5+6)100 + 30 = 10000 + 1100 + 30 = 11130.",
            "pages": [22, 23],
        },
        {
            "q": "(x + y + z)² = ?",
            "options": [
                "A) x² + y² + z² + 2xy + 2yz + 2zx",
                "B) x² + y² + z²",
                "C) x² + y² + z² + xy + yz + zx",
                "D) (x+y)² + z²",
            ],
            "correct": "A",
            "explanation": "Identity: (x + y + z)² = x² + y² + z² + 2xy + 2yz + 2zx.",
            "pages": [24, 25],
        },
        {
            "q": "If x + y + z = 0, then x³ + y³ + z³ = ?",
            "options": ["A) 3xyz", "B) 0", "C) xyz", "D) −3xyz"],
            "correct": "A",
            "explanation": "From x³ + y³ + z³ − 3xyz = (x+y+z)(x²+y²+z²−xy−yz−zx), if x+y+z = 0, then x³+y³+z³ = 3xyz.",
            "pages": [26, 27],
        },
        {
            "q": "(a + b)³ = ?",
            "options": [
                "A) a³ + b³ + 3ab(a + b)",
                "B) a³ + b³",
                "C) a³ + 3a²b + b³",
                "D) a³ − b³ + 3ab(a + b)",
            ],
            "correct": "A",
            "explanation": "Identity: (a + b)³ = a³ + 3a²b + 3ab² + b³ = a³ + b³ + 3ab(a + b).",
            "pages": [24, 25],
        },
        {
            "q": "Factorise x² − y²/100:",
            "options": [
                "A) (x − y/10)(x + y/10)",
                "B) (x − y/100)(x + y/100)",
                "C) (x − y)²/100",
                "D) (x + y/10)²",
            ],
            "correct": "A",
            "explanation": "Using a² − b²: x² − (y/10)² = (x − y/10)(x + y/10).",
            "pages": [22, 23],
        },
        {
            "q": "Evaluate 99² using algebraic identity:",
            "options": ["A) 9801", "B) 9901", "C) 9800", "D) 9701"],
            "correct": "A",
            "explanation": "(100 − 1)² = 100² − 2(100)(1) + 1² = 10000 − 200 + 1 = 9801.",
            "pages": [20, 21],
        },
        {
            "q": "a³ − b³ = ?",
            "options": [
                "A) (a − b)(a² + ab + b²)",
                "B) (a − b)(a² − ab + b²)",
                "C) (a + b)(a² − ab + b²)",
                "D) (a − b)³",
            ],
            "correct": "A",
            "explanation": "Identity: a³ − b³ = (a − b)(a² + ab + b²).",
            "pages": [26, 27],
        },
        {
            "q": "If x + 1/x = 3, then x² + 1/x² = ?",
            "options": ["A) 7", "B) 9", "C) 11", "D) 6"],
            "correct": "A",
            "explanation": "(x + 1/x)² = x² + 2 + 1/x² = 9 → x² + 1/x² = 7.",
            "pages": [20, 21],
        },
    ]

    bank["I'm Up and Down, and Round and Round"] = [
        {
            "q": "A linear equation in two variables has form ax + by + c = 0 where:",
            "options": [
                "A) a and b are not both zero",
                "B) a = 0 and b = 0",
                "C) c = 0 always",
                "D) a = b always",
            ],
            "correct": "A",
            "explanation": "General linear equation: ax + by + c = 0 with a, b both not zero simultaneously.",
            "pages": [30, 31],
        },
        {
            "q": "How many solutions does a linear equation 2x + 3y = 12 have?",
            "options": ["A) Infinitely many", "B) Exactly one", "C) Two", "D) None"],
            "correct": "A",
            "explanation": "A single linear equation in two variables has infinitely many solutions corresponding to points on its line.",
            "pages": [32, 33],
        },
        {
            "q": "The graph of x = 3 is a straight line:",
            "options": [
                "A) Parallel to y-axis at distance 3",
                "B) Parallel to x-axis",
                "C) Passing through origin",
                "D) Slanted at 45°",
            ],
            "correct": "A",
            "explanation": "x = c is a vertical line parallel to the y-axis at distance c units.",
            "pages": [34, 35],
        },
        {
            "q": "The graph of y = 0 represents the:",
            "options": ["A) x-axis", "B) y-axis", "C) Line x = y", "D) Origin"],
            "correct": "A",
            "explanation": "Every point on the x-axis has y = 0. So y = 0 is the equation of the x-axis.",
            "pages": [34, 35],
        },
        {
            "q": "If (2, 0) is a solution of 2x + 3y = k, then k = ?",
            "options": ["A) 4", "B) 6", "C) 2", "D) 0"],
            "correct": "A",
            "explanation": "Substitute x=2, y=0: 2(2) + 3(0) = 4 → k = 4.",
            "pages": [32, 33],
        },
        {
            "q": "The line y = mx passes through:",
            "options": ["A) The origin (0, 0)", "B) (1, 0)", "C) (0, 1)", "D) (m, 0)"],
            "correct": "A",
            "explanation": "When x = 0, y = m(0) = 0. The line always passes through the origin.",
            "pages": [34, 35],
        },
        {
            "q": "The point of the form (a, −a) always lies on the line:",
            "options": ["A) x + y = 0", "B) x − y = 0", "C) y = x", "D) x = 0"],
            "correct": "A",
            "explanation": "a + (−a) = 0. All such points satisfy x + y = 0.",
            "pages": [32, 33],
        },
        {
            "q": "The cost of a notebook is twice the cost of a pen. Linear equation representing this is:",
            "options": ["A) x − 2y = 0", "B) x + 2y = 0", "C) 2x − y = 0", "D) x = y + 2"],
            "correct": "A",
            "explanation": "Let notebook cost = x, pen cost = y. Then x = 2y → x − 2y = 0.",
            "pages": [30, 31],
        },
        {
            "q": "Any point on the line y = x is of the form:",
            "options": ["A) (a, a)", "B) (a, −a)", "C) (0, a)", "D) (a, 0)"],
            "correct": "A",
            "explanation": "On y = x, the x and y coordinates are equal: (a, a).",
            "pages": [34, 35],
        },
        {
            "q": "The equation 2x + 5 = 0 in two variables can be written as:",
            "options": [
                "A) 2x + 0y + 5 = 0",
                "B) 2x + y + 5 = 0",
                "C) 2x + 5y = 0",
                "D) x + 2y + 5 = 0",
            ],
            "correct": "A",
            "explanation": "Written in standard form ax + by + c = 0 with b = 0: 2x + 0y + 5 = 0.",
            "pages": [30, 31],
        },
    ]

    bank["Measuring Space: Perimeter and Area"] = [
        {
            "q": "Heron's formula for the area of a triangle is:",
            "options": [
                "A) √[s(s−a)(s−b)(s−c)]",
                "B) ½ × base × height",
                "C) s(s−a)(s−b)",
                "D) √[s(a+b+c)]",
            ],
            "correct": "A",
            "explanation": "Heron's formula: Area = √[s(s−a)(s−b)(s−c)] where s = (a+b+c)/2.",
            "pages": [36, 37],
        },
        {
            "q": "In Heron's formula, 's' represents:",
            "options": [
                "A) Semi-perimeter",
                "B) Side length",
                "C) Sum of squares",
                "D) Surface area",
            ],
            "correct": "A",
            "explanation": "s = (a + b + c) / 2 is the semi-perimeter of the triangle.",
            "pages": [36, 37],
        },
        {
            "q": "The area of an equilateral triangle with side 'a' is:",
            "options": ["A) (√3/4) a²", "B) (√3/2) a²", "C) ½ a²", "D) √3 a"],
            "correct": "A",
            "explanation": "Using Heron's formula with a = b = c, Area = (√3 / 4) a².",
            "pages": [38, 39],
        },
        {
            "q": "The perimeter of a triangular field is 450 m and sides are in ratio 13:12:5. Area is:",
            "options": ["A) 6750 m²", "B) 9000 m²", "C) 4500 m²", "D) 13500 m²"],
            "correct": "A",
            "explanation": "13x + 12x + 5x = 450 → 30x = 450 → x = 15. Sides: 195, 180, 75. Area = ½ × 75 × 180 = 6750 m².",
            "pages": [38, 39],
        },
        {
            "q": "The sides of a triangle are 3 cm, 4 cm, and 5 cm. Its area is:",
            "options": ["A) 6 cm²", "B) 12 cm²", "C) 10 cm²", "D) 7.5 cm²"],
            "correct": "A",
            "explanation": "It's a right triangle: Area = ½ × 3 × 4 = 6 cm² (or by Heron's formula: s=6, √(6×3×2×1) = 6).",
            "pages": [36, 37],
        },
        {
            "q": "An isosceles right triangle has area 8 cm². Length of its hypotenuse is:",
            "options": ["A) √32 cm", "B) 4 cm", "C) 8 cm", "D) 4√2 cm"],
            "correct": "D",
            "explanation": "½ a² = 8 → a² = 16 → a = 4. Hypotenuse = √(4² + 4²) = √32 = 4√2 cm.",
            "pages": [38, 39],
        },
        {
            "q": "Area of a rhombus whose diagonals are 12 cm and 16 cm is:",
            "options": ["A) 96 cm²", "B) 192 cm²", "C) 48 cm²", "D) 100 cm²"],
            "correct": "A",
            "explanation": "Area of rhombus = ½ × d₁ × d₂ = ½ × 12 × 16 = 96 cm².",
            "pages": [40, 41],
        },
        {
            "q": "If perimeter of an equilateral triangle is 60 cm, its area is:",
            "options": ["A) 100√3 cm²", "B) 200√3 cm²", "C) 400√3 cm²", "D) 50√3 cm²"],
            "correct": "A",
            "explanation": "Side a = 60/3 = 20 cm. Area = (√3/4)(20²) = 100√3 cm².",
            "pages": [38, 39],
        },
        {
            "q": "Area of a parallelogram with base 8 cm and altitude 5 cm is:",
            "options": ["A) 40 cm²", "B) 20 cm²", "C) 80 cm²", "D) 26 cm²"],
            "correct": "A",
            "explanation": "Area of parallelogram = base × height = 8 × 5 = 40 cm².",
            "pages": [40, 41],
        },
        {
            "q": "Area of a trapezium with parallel sides 10 cm, 12 cm and height 4 cm is:",
            "options": ["A) 44 cm²", "B) 88 cm²", "C) 22 cm²", "D) 48 cm²"],
            "correct": "A",
            "explanation": "Area = ½ × (a + b) × h = ½ × (10 + 12) × 4 = 22 × 2 = 44 cm².",
            "pages": [40, 41],
        },
    ]

    bank["The Mathematics of Maybe: Introduction to Probability"] = [
        {
            "q": "Empirical probability is based on:",
            "options": [
                "A) Actual experiments and observations",
                "B) Theoretical assumptions only",
                "C) Pure guesswork",
                "D) Geometry",
            ],
            "correct": "A",
            "explanation": "Empirical (experimental) probability = (Number of trials in which event happened) / (Total number of trials).",
            "pages": [42, 43],
        },
        {
            "q": "A coin is tossed 1000 times with heads occurring 455 times. Empirical probability of head is:",
            "options": ["A) 0.455", "B) 0.545", "C) 0.500", "D) 0.450"],
            "correct": "A",
            "explanation": "P(Head) = 455 / 1000 = 0.455.",
            "pages": [42, 43],
        },
        {
            "q": "The sum of probabilities of all possible outcomes of an experiment is:",
            "options": ["A) 1", "B) 0", "C) 100", "D) Depends on experiment"],
            "correct": "A",
            "explanation": "The sum of probabilities of all elementary events is always 1.",
            "pages": [44, 45],
        },
        {
            "q": "Probability of an event always satisfies:",
            "options": ["A) 0 ≤ P(E) ≤ 1", "B) P(E) > 1", "C) P(E) < 0", "D) −1 ≤ P(E) ≤ 1"],
            "correct": "A",
            "explanation": "Probability is always a real number between 0 and 1 inclusive.",
            "pages": [44, 45],
        },
        {
            "q": "In 500 throws of a die, outcome 3 occurred 80 times. Probability of getting 3 is:",
            "options": ["A) 0.16", "B) 0.20", "C) 0.12", "D) 0.30"],
            "correct": "A",
            "explanation": "P(3) = 80 / 500 = 0.16.",
            "pages": [42, 43],
        },
        {
            "q": "If P(E) = 0.38, then P(not E) = ?",
            "options": ["A) 0.62", "B) 0.38", "C) 0.72", "D) 0.48"],
            "correct": "A",
            "explanation": "P(not E) = 1 − P(E) = 1 − 0.38 = 0.62.",
            "pages": [44, 45],
        },
        {
            "q": "In a cricket match, a batswoman hits boundary 6 times out of 30 balls. Probability she didn't hit boundary:",
            "options": ["A) 4/5", "B) 1/5", "C) 3/5", "D) 2/5"],
            "correct": "A",
            "explanation": "Balls without boundary = 30 − 6 = 24. P = 24 / 30 = 4/5 = 0.8.",
            "pages": [44, 45],
        },
        {
            "q": "An event with probability 0 is called:",
            "options": [
                "A) Impossible event",
                "B) Certain event",
                "C) Rare event",
                "D) Likely event",
            ],
            "correct": "A",
            "explanation": "An event that cannot happen has probability 0 — an impossible event.",
            "pages": [44, 45],
        },
        {
            "q": "Three coins are tossed simultaneously 200 times. 2 heads appear 72 times. P(2 heads) is:",
            "options": ["A) 0.36", "B) 0.72", "C) 0.28", "D) 0.18"],
            "correct": "A",
            "explanation": "P(2 heads) = 72 / 200 = 0.36 = 9/25.",
            "pages": [42, 43],
        },
        {
            "q": "As the number of trials in a probability experiment increases, the empirical probability:",
            "options": [
                "A) Approaches theoretical probability",
                "B) Becomes zero",
                "C) Becomes 1",
                "D) Oscillates wildly",
            ],
            "correct": "A",
            "explanation": "Law of Large Numbers: experimental probability approaches theoretical probability as trials increase.",
            "pages": [44, 45],
        },
    ]

    bank["Predicting What Comes Next: Exploring Sequences and Progressions"] = [
        {
            "q": "A sequence where the difference between consecutive terms is constant is called an:",
            "options": [
                "A) Arithmetic Progression",
                "B) Geometric Progression",
                "C) Harmonic Progression",
                "D) Fibonacci Sequence",
            ],
            "correct": "A",
            "explanation": "An AP has constant difference d = aₙ − aₙ₋₁ between consecutive terms.",
            "pages": [46, 47],
        },
        {
            "q": "The next term in sequence 2, 5, 8, 11, ... is:",
            "options": ["A) 14", "B) 13", "C) 15", "D) 16"],
            "correct": "A",
            "explanation": "Common difference d = 3. Next term = 11 + 3 = 14.",
            "pages": [46, 47],
        },
        {
            "q": "The general term (nth term) of sequence 3, 7, 11, 15, ... is:",
            "options": ["A) 4n − 1", "B) 4n + 1", "C) 3n + 1", "D) 4n − 3"],
            "correct": "A",
            "explanation": "a = 3, d = 4. aₙ = 3 + (n−1)4 = 4n − 1.",
            "pages": [48, 49],
        },
        {
            "q": "In Fibonacci sequence 1, 1, 2, 3, 5, 8, ..., each term is the sum of:",
            "options": [
                "A) Preceding two terms",
                "B) All preceding terms",
                "C) First two terms",
                "D) Preceding three terms",
            ],
            "correct": "A",
            "explanation": "Fibonacci rule: Fₙ = Fₙ₋₁ + Fₙ₋₂.",
            "pages": [50, 51],
        },
        {
            "q": "The pattern 1, 4, 9, 16, 25 represents:",
            "options": [
                "A) Square numbers (n²)",
                "B) Triangular numbers",
                "C) Cube numbers",
                "D) Prime numbers",
            ],
            "correct": "A",
            "explanation": "These are perfect squares: 1², 2², 3², 4², 5².",
            "pages": [46, 47],
        },
        {
            "q": "If a sequence has rule aₙ = 2n + 3, the 10th term is:",
            "options": ["A) 23", "B) 20", "C) 25", "D) 21"],
            "correct": "A",
            "explanation": "a₁₀ = 2(10) + 3 = 23.",
            "pages": [48, 49],
        },
        {
            "q": "The common difference of sequence 10, 6, 2, −2, ... is:",
            "options": ["A) −4", "B) 4", "C) −6", "D) 6"],
            "correct": "A",
            "explanation": "d = 6 − 10 = −4.",
            "pages": [46, 47],
        },
        {
            "q": "Which sequence shows exponential growth?",
            "options": [
                "A) 2, 4, 8, 16, 32",
                "B) 2, 4, 6, 8, 10",
                "C) 1, 3, 5, 7, 9",
                "D) 10, 20, 30, 40",
            ],
            "correct": "A",
            "explanation": "2, 4, 8, 16, 32 is geometric/exponential (each term multiplied by 2).",
            "pages": [50, 51],
        },
        {
            "q": "The sum of first 5 terms of 2, 4, 6, 8, 10 is:",
            "options": ["A) 30", "B) 25", "C) 32", "D) 28"],
            "correct": "A",
            "explanation": "2 + 4 + 6 + 8 + 10 = 30.",
            "pages": [48, 49],
        },
        {
            "q": "Triangular numbers are: 1, 3, 6, 10, ... The 5th triangular number is:",
            "options": ["A) 15", "B) 12", "C) 20", "D) 16"],
            "correct": "A",
            "explanation": "Tₙ = n(n+1)/2. T₅ = 5(6)/2 = 15.",
            "pages": [50, 51],
        },
    ]

    return bank


# ---------------------------------------------------------------------------
# STUDENT PROFILES — Realistic personality/performance profiles
# ---------------------------------------------------------------------------

STUDENT_PROFILES = {
    # Class 9 students
    "F4GCqF4risTGuYSEWVnKqMC0sTH2": {
        "name": "Anjali Desai",
        "class": 9,
        "archetype": "consistent_performer",
        "sci_strength": 0.72,
        "math_strength": 0.68,
    },
    "mKr5o8w9hCMJkuJMMy475AVib2C3": {
        "name": "Arun Verma",
        "class": 9,
        "archetype": "math_oriented",
        "sci_strength": 0.55,
        "math_strength": 0.82,
    },
    "qCjqQ5kvwrTJ2sPwTQDFMUKJTxN2": {
        "name": "Divya Patel",
        "class": 9,
        "archetype": "science_star",
        "sci_strength": 0.85,
        "math_strength": 0.60,
    },
    "ZhfpbyBUpxW2E190TMn5plRm9Zt2": {
        "name": "Karan Singh",
        "class": 9,
        "archetype": "struggling",
        "sci_strength": 0.42,
        "math_strength": 0.38,
    },
    "kVuj9SQ3Q1OL36Shjlq0BDbGyqh1": {
        "name": "Megha Iyer",
        "class": 9,
        "archetype": "improving",
        "sci_strength": 0.58,
        "math_strength": 0.62,
    },
    "uIdz3GK7hTcDcBSTzx8etLOM0zR2": {
        "name": "Priya Sharma",
        "class": 9,
        "archetype": "topper",
        "sci_strength": 0.90,
        "math_strength": 0.88,
    },
    "eQzn4Qdc1gS30JBP2PRhSMcWeTm2": {
        "name": "Rahul Nair",
        "class": 9,
        "archetype": "average",
        "sci_strength": 0.55,
        "math_strength": 0.52,
    },
    "0PxRNJlUzZXv77ys49K5bMGoyJV2": {
        "name": "Rohit Kumar",
        "class": 9,
        "archetype": "inconsistent",
        "sci_strength": 0.65,
        "math_strength": 0.60,
    },
    "KOU2w0tEaINRKP2fwSeY283OWmA3": {
        "name": "Sneha Gupta",
        "class": 9,
        "archetype": "hard_worker",
        "sci_strength": 0.70,
        "math_strength": 0.75,
    },
    "6M47gpi9Glhpawjevj8VaUbei7f2": {
        "name": "Vikram Rao",
        "class": 9,
        "archetype": "declining",
        "sci_strength": 0.50,
        "math_strength": 0.45,
    },
    # Class 10 students
    "KpcJRCq2yVOy16QZVazs48BcjiO2": {
        "name": "Amit Shah",
        "class": 10,
        "archetype": "consistent_performer",
        "sci_strength": 0.70,
        "math_strength": 0.72,
    },
    "kyXujnjq6WN3XbEpqkweU2Ak5h73": {
        "name": "Deepak Mishra",
        "class": 10,
        "archetype": "topper",
        "sci_strength": 0.92,
        "math_strength": 0.90,
    },
    "ftg27gSZniYAp9qHD57dnrjp6Yk1": {
        "name": "Kavita Menon",
        "class": 10,
        "archetype": "science_star",
        "sci_strength": 0.88,
        "math_strength": 0.62,
    },
    "y5QV97Uw3fSDpA6bGqFArLwm6ly1": {
        "name": "Manish Tiwari",
        "class": 10,
        "archetype": "struggling",
        "sci_strength": 0.40,
        "math_strength": 0.35,
    },
    "jwoiqESdPmT4p89WOpzQYFMIfYx2": {
        "name": "Neha Joshi",
        "class": 10,
        "archetype": "math_oriented",
        "sci_strength": 0.58,
        "math_strength": 0.85,
    },
    "gVMvcZdp4TULJ1NTrmO8AZHCJS92": {
        "name": "Pooja Bhat",
        "class": 10,
        "archetype": "improving",
        "sci_strength": 0.55,
        "math_strength": 0.60,
    },
    "PTWWGtt5mVeN6djNvYd6VRmiya73": {
        "name": "Raj Chouhan",
        "class": 10,
        "archetype": "average",
        "sci_strength": 0.52,
        "math_strength": 0.55,
    },
    "EVWd8Ocpa7PhpE0Thx0mAsoB0Yv1": {
        "name": "Ritu Pandey",
        "class": 10,
        "archetype": "hard_worker",
        "sci_strength": 0.75,
        "math_strength": 0.78,
    },
    "tKPa2wooIResOgyKmBLbZjUn4RG2": {
        "name": "Suresh Reddy",
        "class": 10,
        "archetype": "inconsistent",
        "sci_strength": 0.60,
        "math_strength": 0.55,
    },
    "WMt1XnASrwRreQBSZjcQaWdBqfk2": {
        "name": "Swati Yadav",
        "class": 10,
        "archetype": "declining",
        "sci_strength": 0.48,
        "math_strength": 0.42,
    },
}


# ---------------------------------------------------------------------------
# QUIZ ATTEMPT GENERATION — Realistic quiz performance simulation
# ---------------------------------------------------------------------------


def simulate_quiz_attempt(
    student_id, profile, chapter_info, subject, question_bank, quiz_date, difficulty
):
    """
    Simulate a realistic quiz attempt for a student.
    Returns quiz_id, quiz_data, and question_responses.
    """
    quiz_id = f"quiz_{quiz_date.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    chapter = chapter_info["chapter"]
    chapter_number = chapter_info["chapter_number"]
    concepts = chapter_info["concepts"]

    # Get questions from bank
    available_questions = question_bank.get(chapter, [])
    if not available_questions:
        return None

    # Pick 10 questions (with possible repeats if bank is small)
    total_q = 10
    questions = []
    if len(available_questions) >= total_q:
        questions = random.sample(available_questions, total_q)
    else:
        questions = available_questions.copy()
        while len(questions) < total_q:
            questions.append(random.choice(available_questions))

    # Determine base accuracy based on profile and subject
    if subject == "Science":
        base_strength = profile["sci_strength"]
    else:
        base_strength = profile["math_strength"]

    # Modify based on difficulty
    difficulty_modifier = {"easy": 0.15, "medium": 0.0, "hard": -0.15}
    effective_strength = base_strength + difficulty_modifier.get(difficulty, 0)

    # Apply archetype modifiers for realism
    archetype = profile["archetype"]
    if archetype == "improving":
        # Later quizzes are better — this date-dependent modifier is handled by caller
        pass
    elif archetype == "declining":
        pass
    elif archetype == "inconsistent":
        effective_strength += random.uniform(-0.15, 0.15)

    effective_strength = max(0.15, min(0.95, effective_strength))

    # Simulate answers
    score = 0
    responses = []
    for idx, q in enumerate(questions, 1):
        concept = random.choice(concepts) if concepts else f"concept_{random.randint(1, 50)}"

        # Determine if student gets it right
        is_correct = random.random() < effective_strength

        correct_answer = q["correct"]
        if is_correct:
            user_answer = correct_answer
        else:
            wrong_options = [opt for opt in ["A", "B", "C", "D"] if opt != correct_answer]
            user_answer = random.choice(wrong_options)

        if is_correct:
            score += 1

        responses.append(
            {
                "quiz_id": quiz_id,
                "question_id": f"{quiz_id}_q{idx}",
                "question_text": q["q"],
                "chapter": chapter,
                "difficulty": difficulty,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": 1 if is_correct else 0,
                "source_pages": json.dumps(q.get("pages", [])),
                "concept_id": concept,
            }
        )

    percentage = (score / total_q) * 100.0
    timestamp = quiz_date.isoformat()

    quiz_attempt = {
        "quiz_id": quiz_id,
        "student_id": student_id,
        "class_level": profile["class"],
        "subject": subject,
        "chapter": chapter,
        "chapter_number": chapter_number,
        "difficulty": difficulty,
        "score": score,
        "total_questions": total_q,
        "percentage": round(percentage, 2),
        "timestamp": timestamp,
    }

    return quiz_attempt, responses


# ---------------------------------------------------------------------------
# ACTION PLAN GENERATION
# ---------------------------------------------------------------------------


def generate_action_plan_data(student_id, class_level, subject, quiz_attempts):
    """Generate a realistic teacher action plan based on quiz performance."""
    # Aggregate per chapter
    chapter_stats = {}
    for qa in quiz_attempts:
        if qa["subject"] == subject and qa["student_id"] == student_id:
            ch = qa["chapter"]
            if ch not in chapter_stats:
                chapter_stats[ch] = {
                    "total_score": 0,
                    "total_q": 0,
                    "attempts": 0,
                    "chapter_number": qa["chapter_number"],
                }
            chapter_stats[ch]["total_score"] += qa["score"]
            chapter_stats[ch]["total_q"] += qa["total_questions"]
            chapter_stats[ch]["attempts"] += 1

    actions = []
    for ch, stats in sorted(
        chapter_stats.items(), key=lambda x: x[1]["total_score"] / max(x[1]["total_q"], 1)
    ):
        accuracy = round((stats["total_score"] / max(stats["total_q"], 1)) * 100, 1)
        if accuracy < 50:
            priority = "high"
            action_type = "practice_weak"
            recommendation = f"Focus on revising {ch}. Attempt easy-to-medium quizzes. Review NCERT solved examples."
        elif accuracy < 70:
            priority = "medium"
            action_type = "reinforce"
            recommendation = f"Reinforce understanding of {ch}. Try medium difficulty quizzes. Practice numerical problems."
        else:
            priority = "low"
            action_type = "challenge"
            recommendation = (
                f"Good command of {ch}. Attempt hard quizzes and HOTS questions for mastery."
            )

        actions.append(
            {
                "chapter": ch,
                "chapter_number": stats["chapter_number"],
                "priority": priority,
                "action_type": action_type,
                "accuracy": accuracy,
                "attempts": stats["attempts"],
                "recommendation": recommendation,
            }
        )

    plan = {
        "student_id": student_id,
        "class_level": class_level,
        "subject": subject,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_chapters_attempted": len(chapter_stats),
        "actions": sorted(actions, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]]),
        "overall_recommendation": "Focus on weak chapters first, then reinforce average topics.",
    }

    return json.dumps(plan)


# ---------------------------------------------------------------------------
# STUDY TWIN MATCH GENERATION
# ---------------------------------------------------------------------------


def generate_study_twin_matches(all_quiz_attempts, student_profiles):
    """Generate realistic study twin matches between students of the same class."""
    matches = []
    # Group by class_level
    class_groups = {}
    for sid, prof in student_profiles.items():
        cl = prof["class"]
        if cl not in class_groups:
            class_groups[cl] = []
        class_groups[cl].append(sid)

    for cl, students in class_groups.items():
        for subject in ["Science", "Mathematics"]:
            # Build chapter performance for each student
            student_chapters = {}
            for sid in students:
                chapters_attempted = set()
                weak = set()
                for qa in all_quiz_attempts:
                    if qa["student_id"] == sid and qa["subject"] == subject:
                        chapters_attempted.add(qa["chapter"])
                        if qa["percentage"] < 50:
                            weak.add(qa["chapter"])
                student_chapters[sid] = {"attempted": chapters_attempted, "weak": weak}

            # Create matches (best match per student)
            for i, sid in enumerate(students):
                best_match = None
                best_score = -1
                for j, other_sid in enumerate(students):
                    if i == j:
                        continue
                    # Compute similarity
                    s1 = student_chapters.get(sid, {"attempted": set(), "weak": set()})
                    s2 = student_chapters.get(other_sid, {"attempted": set(), "weak": set()})

                    overlap_attempted = len(s1["attempted"] & s2["attempted"])
                    union_attempted = len(s1["attempted"] | s2["attempted"]) or 1
                    overlap_weak = len(s1["weak"] & s2["weak"])
                    union_weak = len(s1["weak"] | s2["weak"]) or 1

                    sim = (
                        overlap_attempted / union_attempted * 0.5 + overlap_weak / union_weak * 0.5
                    ) * 100
                    sim += random.uniform(-5, 10)  # Add some noise
                    sim = max(25, min(95, sim))

                    if sim > best_score:
                        best_score = sim
                        best_match = other_sid

                if best_match:
                    shared_weak = list(
                        student_chapters.get(sid, {"weak": set()})["weak"]
                        & student_chapters.get(best_match, {"weak": set()})["weak"]
                    )
                    shared_chapters = list(
                        student_chapters.get(sid, {"attempted": set()})["attempted"]
                        & student_chapters.get(best_match, {"attempted": set()})["attempted"]
                    )

                    match_data = {
                        "shared_weak_topics": shared_weak[:5],
                        "shared_current_chapters": shared_chapters[:5],
                        "shared_action_goals": [f"Improve {ch}" for ch in shared_weak[:3]],
                        "component_scores": {
                            "chapter_overlap": round(random.uniform(40, 80), 1),
                            "weak_topic_alignment": round(random.uniform(30, 70), 1),
                            "mastery_distance": round(random.uniform(20, 60), 1),
                        },
                        "explanation": f"Both students are working on similar chapters in {subject} and share common areas needing improvement.",
                    }

                    matches.append(
                        {
                            "student_id": sid,
                            "twin_student_id": best_match,
                            "class_level": cl,
                            "subject": subject,
                            "similarity_score": round(best_score, 2),
                            "match_data": json.dumps(match_data),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

    return matches


# ---------------------------------------------------------------------------
# UPLOADED DOCUMENTS GENERATION
# ---------------------------------------------------------------------------


def generate_uploaded_documents(student_id, profile, chapters):
    """Generate realistic uploaded document records."""
    docs = []
    num_docs = random.randint(2, 5)
    selected_chapters = random.sample(chapters, min(num_docs, len(chapters)))

    for ch_info in selected_chapters:
        ch = ch_info["chapter"]
        doc_id = str(uuid.uuid4())
        material_names = [
            f"NCERT {ch} Notes",
            f"{ch} Summary",
            f"{ch} Practice Questions",
            f"Handwritten Notes - {ch}",
            f"{ch} Revision Sheet",
        ]
        filename_base = ch.replace(" ", "_").replace("–", "-").replace("'", "").replace("?", "")

        days_ago = random.randint(5, 60)
        docs.append(
            {
                "document_id": doc_id,
                "student_id": student_id,
                "filename": f"{filename_base}_{random.choice(['notes', 'summary', 'practice'])}.pdf",
                "material_name": random.choice(material_names),
                "class_level": profile["class"],
                "subject": "Science"
                if ch_info in (CLASS_9_SCIENCE + CLASS_10_SCIENCE)
                else "Mathematics",
                "chapter": ch,
                "status": random.choice(["PROCESSED", "PROCESSED", "PROCESSED", "PROCESSING"]),
                "error_message": None,
                "page_count": random.randint(3, 25),
                "chunk_count": random.randint(8, 60),
                "file_size_bytes": random.randint(150000, 8000000),
                "uploaded_at": (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(),
            }
        )

    return docs


# ===========================================================================
# MAIN SEED FUNCTION
# ===========================================================================


def seed():
    question_bank = _make_question_bank()
    conn = get_conn()
    cur = conn.cursor()

    print("=" * 60)
    print("  DiligentEdu Production Seed Script")
    print("=" * 60)

    # ── Step 0: ENSURE DEMO USERS EXIST ──────────────────────────────
    print("\n[0/6] Ensuring core demo users exist...")
    demo_users = [
        (
            "0Z15gOPRLdWCGcf2dricVjOScTI3",
            "student@diligentedu.com",
            "Test Student",
            "student",
            None,
            10,
        ),
        (
            "Rk6Abnn5ANQjnhejbUa4poGbvsJ2",
            "teacher@diligentedu.com",
            "Test Teacher",
            "teacher",
            "science",
            None,
        ),
    ]
    user_upsert_sql = """
        INSERT INTO "User" (id, email, name, role, subject, class_level)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            email = EXCLUDED.email,
            name = EXCLUDED.name,
            role = EXCLUDED.role,
            subject = EXCLUDED.subject,
            class_level = EXCLUDED.class_level;
    """
    for u in demo_users:
        cur.execute(user_upsert_sql, u)
    conn.commit()

    # Load all students from the database
    cur.execute("SELECT id, email, name, class_level FROM \"User\" WHERE role = 'student';")
    db_students = cur.fetchall()
    print(f"  ✓ Loaded {len(db_students)} student accounts from database.")

    # Build student profiles
    archetype_cycle = [
        ("consistent_performer", 0.72, 0.70),
        ("math_oriented", 0.55, 0.84),
        ("science_star", 0.86, 0.58),
        ("improving", 0.56, 0.60),
        ("topper", 0.92, 0.90),
        ("hard_worker", 0.76, 0.78),
        ("inconsistent", 0.62, 0.58),
        ("struggling", 0.42, 0.38),
        ("average", 0.54, 0.52),
        ("declining", 0.50, 0.45),
    ]

    active_student_profiles = {}
    for idx, (sid, email, name, class_level) in enumerate(db_students):
        cl = class_level if class_level in (9, 10) else 10
        if sid in STUDENT_PROFILES:
            prof = dict(STUDENT_PROFILES[sid])
            prof["class"] = cl
            if name:
                prof["name"] = name
            active_student_profiles[sid] = prof
        else:
            arch_name, s_sci, s_math = archetype_cycle[idx % len(archetype_cycle)]
            active_student_profiles[sid] = {
                "name": name or email.split("@")[0].replace(".", " ").title(),
                "class": cl,
                "archetype": arch_name,
                "sci_strength": s_sci,
                "math_strength": s_math,
            }

    # ── Step 1: WIPE ALL SEEDED DATA ─────────────────────────────────
    print("\n[1/6] Wiping existing seeded data...")
    cur.execute('DELETE FROM "QuestionResponse";')
    cur.execute('DELETE FROM "QuizAttempt";')
    cur.execute('DELETE FROM "TeacherActionPlan";')
    cur.execute('DELETE FROM "StudyTwinMatch";')
    cur.execute('DELETE FROM "UploadedDocument";')
    conn.commit()
    print(
        "  ✓ All QuestionResponse, QuizAttempt, TeacherActionPlan, StudyTwinMatch, UploadedDocument wiped."
    )

    # ── Step 2: GENERATE QUIZ ATTEMPTS ──────────────────────────────
    print("\n[2/6] Generating realistic quiz attempts (15-30 per student, both subjects)...")
    all_quiz_attempts = []
    all_responses = []

    for student_id, profile in active_student_profiles.items():
        cl = profile["class"]
        if cl == 9:
            sci_chapters = CLASS_9_SCIENCE
            math_chapters = CLASS_9_MATH
        else:
            sci_chapters = CLASS_10_SCIENCE
            math_chapters = CLASS_10_MATH

        # Determine total quizzes (15-30)
        total_quizzes = random.randint(15, 30)
        sci_quizzes = random.randint(int(total_quizzes * 0.35), int(total_quizzes * 0.65))
        math_quizzes = total_quizzes - sci_quizzes

        difficulties = ["easy", "medium", "hard"]
        diff_weights_normal = [0.25, 0.50, 0.25]
        diff_weights_struggling = [0.45, 0.40, 0.15]
        diff_weights_topper = [0.15, 0.35, 0.50]

        archetype = profile["archetype"]
        if archetype in ("struggling",):
            d_weights = diff_weights_struggling
        elif archetype in ("topper",):
            d_weights = diff_weights_topper
        else:
            d_weights = diff_weights_normal

        student_quizzes = 0

        # Science quizzes
        sci_picked = random.choices(sci_chapters, k=sci_quizzes)
        for i, ch_info in enumerate(sci_picked):
            days_ago = random.randint(1, 75)

            # For 'improving' archetype, more recent quizzes are better
            if archetype == "improving":
                profile_copy = dict(profile)
                improvement = (75 - days_ago) / 75 * 0.15
                profile_copy["sci_strength"] = min(0.95, profile["sci_strength"] + improvement)
            elif archetype == "declining":
                profile_copy = dict(profile)
                decline = (75 - days_ago) / 75 * 0.12
                profile_copy["sci_strength"] = max(0.20, profile["sci_strength"] - decline)
            else:
                profile_copy = profile

            diff = random.choices(difficulties, weights=d_weights, k=1)[0]
            quiz_date = datetime.now(timezone.utc) - timedelta(
                days=days_ago, hours=random.randint(0, 12), minutes=random.randint(0, 59)
            )

            result = simulate_quiz_attempt(
                student_id, profile_copy, ch_info, "Science", question_bank, quiz_date, diff
            )
            if result:
                qa, resps = result
                all_quiz_attempts.append(qa)
                all_responses.extend(resps)
                student_quizzes += 1

        # Math quizzes
        math_picked = random.choices(math_chapters, k=math_quizzes)
        for i, ch_info in enumerate(math_picked):
            days_ago = random.randint(1, 75)

            if archetype == "improving":
                profile_copy = dict(profile)
                improvement = (75 - days_ago) / 75 * 0.15
                profile_copy["math_strength"] = min(0.95, profile["math_strength"] + improvement)
            elif archetype == "declining":
                profile_copy = dict(profile)
                decline = (75 - days_ago) / 75 * 0.12
                profile_copy["math_strength"] = max(0.20, profile["math_strength"] - decline)
            else:
                profile_copy = profile

            diff = random.choices(difficulties, weights=d_weights, k=1)[0]
            quiz_date = datetime.now(timezone.utc) - timedelta(
                days=days_ago, hours=random.randint(0, 12), minutes=random.randint(0, 59)
            )

            result = simulate_quiz_attempt(
                student_id, profile_copy, ch_info, "Mathematics", question_bank, quiz_date, diff
            )
            if result:
                qa, resps = result
                all_quiz_attempts.append(qa)
                all_responses.extend(resps)
                student_quizzes += 1

        print(f"  {profile['name']:25s} (Class {cl}) → {student_quizzes} quizzes")

    # ── Step 3: INSERT QUIZ ATTEMPTS & RESPONSES ────────────────────
    print(
        f"\n[3/6] Inserting {len(all_quiz_attempts)} quiz attempts and {len(all_responses)} question responses..."
    )

    quiz_sql = """
        INSERT INTO "QuizAttempt" (quiz_id, student_id, class_level, subject, chapter, chapter_number, difficulty, score, total_questions, percentage, timestamp)
        VALUES %s
    """
    quiz_values = [
        (
            qa["quiz_id"],
            qa["student_id"],
            qa["class_level"],
            qa["subject"],
            qa["chapter"],
            qa["chapter_number"],
            qa["difficulty"],
            qa["score"],
            qa["total_questions"],
            qa["percentage"],
            qa["timestamp"],
        )
        for qa in all_quiz_attempts
    ]
    execute_values(cur, quiz_sql, quiz_values, page_size=200)

    resp_sql = """
        INSERT INTO "QuestionResponse" (quiz_id, question_id, question_text, chapter, difficulty, user_answer, correct_answer, is_correct, source_pages, concept_id)
        VALUES %s
    """
    resp_values = [
        (
            r["quiz_id"],
            r["question_id"],
            r["question_text"],
            r["chapter"],
            r["difficulty"],
            r["user_answer"],
            r["correct_answer"],
            r["is_correct"],
            r["source_pages"],
            r["concept_id"],
        )
        for r in all_responses
    ]
    # Insert in batches
    batch_size = 500
    for i in range(0, len(resp_values), batch_size):
        execute_values(cur, resp_sql, resp_values[i : i + batch_size], page_size=200)

    conn.commit()
    print(f"  ✓ {len(all_quiz_attempts)} quiz attempts inserted.")
    print(f"  ✓ {len(all_responses)} question responses inserted.")

    # ── Step 4: INSERT ACTION PLANS ─────────────────────────────────
    print("\n[4/6] Generating and inserting teacher action plans...")
    action_plans = []
    for student_id, profile in active_student_profiles.items():
        cl = profile["class"]
        for subject in ["Science", "Mathematics"]:
            plan_data = generate_action_plan_data(student_id, cl, subject, all_quiz_attempts)
            teacher_notes_options = [
                None,
                "Please focus more on weak chapters. Regular practice needed.",
                f"Good progress in {subject}. Keep up the effort!",
                "Recommend extra coaching for low-scoring chapters.",
                "Student shows potential but needs consistency.",
                "Encourage participation in chapter-wise tests.",
            ]
            action_plans.append(
                {
                    "student_id": student_id,
                    "class_level": cl,
                    "subject": subject,
                    "plan_data": plan_data,
                    "teacher_notes": random.choice(teacher_notes_options),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    plan_sql = """
        INSERT INTO "TeacherActionPlan" (student_id, class_level, subject, plan_data, teacher_notes, updated_at)
        VALUES %s
        ON CONFLICT (student_id, class_level, subject) DO UPDATE SET
            plan_data = EXCLUDED.plan_data,
            teacher_notes = EXCLUDED.teacher_notes,
            updated_at = EXCLUDED.updated_at
    """
    plan_values = [
        (
            ap["student_id"],
            ap["class_level"],
            ap["subject"],
            ap["plan_data"],
            ap["teacher_notes"],
            ap["updated_at"],
        )
        for ap in action_plans
    ]
    execute_values(cur, plan_sql, plan_values, page_size=50)
    conn.commit()
    print(f"  ✓ {len(action_plans)} action plans inserted.")

    # ── Step 5: INSERT STUDY TWIN MATCHES ───────────────────────────
    print("\n[5/6] Computing and inserting study twin matches...")
    twin_matches = generate_study_twin_matches(all_quiz_attempts, active_student_profiles)

    twin_sql = """
        INSERT INTO "StudyTwinMatch" (student_id, twin_student_id, class_level, subject, similarity_score, match_data, created_at)
        VALUES %s
        ON CONFLICT (student_id, class_level, subject) DO UPDATE SET
            twin_student_id = EXCLUDED.twin_student_id,
            similarity_score = EXCLUDED.similarity_score,
            match_data = EXCLUDED.match_data,
            created_at = EXCLUDED.created_at
    """
    twin_values = [
        (
            tm["student_id"],
            tm["twin_student_id"],
            tm["class_level"],
            tm["subject"],
            tm["similarity_score"],
            tm["match_data"],
            tm["created_at"],
        )
        for tm in twin_matches
    ]
    execute_values(cur, twin_sql, twin_values, page_size=50)
    conn.commit()
    print(f"  ✓ {len(twin_matches)} study twin matches inserted.")

    # ── Step 6: INSERT UPLOADED DOCUMENTS ───────────────────────────
    print("\n[6/6] Generating and inserting uploaded documents...")
    all_docs = []
    for student_id, profile in active_student_profiles.items():
        cl = profile["class"]
        if cl == 9:
            chapters = CLASS_9_SCIENCE + CLASS_9_MATH
        else:
            chapters = CLASS_10_SCIENCE + CLASS_10_MATH
        docs = generate_uploaded_documents(student_id, profile, chapters)
        all_docs.extend(docs)

    doc_sql = """
        INSERT INTO "UploadedDocument" (document_id, student_id, filename, material_name, class_level, subject, chapter, status, error_message, page_count, chunk_count, file_size_bytes, uploaded_at)
        VALUES %s
        ON CONFLICT (document_id) DO NOTHING
    """
    doc_values = [
        (
            d["document_id"],
            d["student_id"],
            d["filename"],
            d["material_name"],
            d["class_level"],
            d["subject"],
            d["chapter"],
            d["status"],
            d["error_message"],
            d["page_count"],
            d["chunk_count"],
            d["file_size_bytes"],
            d["uploaded_at"],
        )
        for d in all_docs
    ]
    execute_values(cur, doc_sql, doc_values, page_size=100)
    conn.commit()
    print(f"  ✓ {len(all_docs)} uploaded documents inserted.")

    # ── SUMMARY ─────────────────────────────────────────────────────
    cur.execute('SELECT COUNT(*) FROM "QuizAttempt";')
    qa_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM "QuestionResponse";')
    qr_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM "TeacherActionPlan";')
    ap_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM "StudyTwinMatch";')
    tw_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM "UploadedDocument";')
    doc_count = cur.fetchone()[0]

    print("\n" + "=" * 60)
    print("  SEED COMPLETE — Summary")
    print("=" * 60)
    print(f"  Quiz Attempts:       {qa_count}")
    print(f"  Question Responses:  {qr_count}")
    print(f"  Teacher Action Plans: {ap_count}")
    print(f"  Study Twin Matches:  {tw_count}")
    print(f"  Uploaded Documents:  {doc_count}")
    print(
        f"  Students (Class 9):  {sum(1 for p in active_student_profiles.values() if p['class'] == 9)}"
    )
    print(
        f"  Students (Class 10): {sum(1 for p in active_student_profiles.values() if p['class'] == 10)}"
    )
    print("=" * 60)

    # Verify class level separation
    cur.execute("""
        SELECT u.class_level, qa.class_level, COUNT(*)
        FROM "QuizAttempt" qa
        JOIN "User" u ON u.id = qa.student_id
        WHERE u.class_level != qa.class_level
        GROUP BY u.class_level, qa.class_level;
    """)
    mismatches = cur.fetchall()
    if mismatches:
        print(f"\n  ⚠ Class level mismatches found: {mismatches}")
    else:
        print("\n  ✓ Class level integrity verified: no cross-class content leaks.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    seed()
