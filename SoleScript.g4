// SoleScript.g4
// ANTLR4 grammar for SoleScript DSL
// Orthopedic Footwear Pattern DSL  FAF-241, Team 3
//
// To generate the parser (requires ANTLR4 tool):
//   java -jar antlr-4.x-complete.jar -Dlanguage=Python3 -visitor SoleScript.g4
//
// Then install the runtime:
//   pip install antlr4-python3-runtime==4.x

grammar SoleScript;

// ─────────────────────────────────────────
// Parser Rules (G1–G11)
// ─────────────────────────────────────────

// G1: program → statement*
program
    : statement* EOF
    ;

// G2: statement → foot_decl | obs_decl | last_decl | boot_decl | export_decl
statement
    : foot_decl
    | obs_decl
    | last_decl
    | boot_decl
    | export_decl
    ;

// G3: foot_decl → Foot id '{' attr_list '}'
foot_decl
    : FOOT id LBRACE attr_list RBRACE
    ;

// G4: obs_decl → Observations id '{' attr_list '}'
obs_decl
    : OBSERVATIONS id LBRACE attr_list RBRACE
    ;

// G5: last_decl → Last id '{' attr_list '}'
last_decl
    : LAST id LBRACE attr_list RBRACE
    ;

// G6: boot_decl → Boot id '{' attr_list comp_list '}'
boot_decl
    : BOOT id LBRACE attr_list comp_list RBRACE
    ;

// G7: export_decl → Export id
export_decl
    : EXPORT id
    ;

// G8: attr_list → (id ':' value)*
attr_list
    : attr_entry*
    ;

attr_entry
    : id COLON value
    ;

// G9: comp_list → (shoe_comp '{' '}')*
comp_list
    : comp_entry*
    ;

comp_entry
    : shoe_comp LBRACE RBRACE
    ;

// G10: shoe_comp → Vamp | Tongue | Quarter | ToeBox | Outsole | Heel | Shank | Insole | Counter | Lining
shoe_comp
    : VAMP
    | TONGUE
    | QUARTER
    | TOEBOX
    | OUTSOLE
    | HEEL
    | SHANK
    | INSOLE
    | COUNTER
    | LINING
    ;

// G11: value → number ('mm'|'cm') | id | '[' string+ ']' | keyword_val
value
    : number UNIT                    # dimensionValue
    | id                             # idValue
    | LBRACKET string_val+ RBRACKET  # stringListValue
    | keyword_val                    # keywordValue
    ;

// G12: id → (letter|'_')(alphanumeric|'_')*  — captured by lexer rule ID
id
    : ID
    ;

// G13: number → digit+ ('.' digit+)?  — captured by lexer rule NUMBER
number
    : NUMBER
    ;

// G15: string → '"' (any char except '"')* '"'
string_val
    : STRING
    ;

// G16: keyword_val → Diabetic | Egyptian | Greek | Roman | ...
keyword_val
    : DIABETIC
    | EGYPTIAN
    | GREEK
    | ROMAN
    | CELTIC
    | GERMANIC
    | SQUARE
    | PEASANT
    ;

// ─────────────────────────────────────────
// Lexer Rules  (G14 + Lexical Rules section)
// ─────────────────────────────────────────

// Reserved keywords (case-sensitive)
FOOT         : 'Foot' ;
OBSERVATIONS : 'Observations' ;
LAST         : 'Last' ;
BOOT         : 'Boot' ;
EXPORT       : 'Export' ;

// Shoe component keywords
VAMP    : 'Vamp' ;
TONGUE  : 'Tongue' ;
QUARTER : 'Quarter' [0-9]* ;   // "Quarter 1", "Quarter 2", etc.
TOEBOX  : 'ToeBox' ;
OUTSOLE : 'Outsole' ;
HEEL    : 'Heel' ;
SHANK   : 'Shank' ;
INSOLE  : 'Insole' ;
COUNTER : 'Counter' ;
LINING  : 'Lining' ;

// Keyword values (G16)
DIABETIC  : 'Diabetic' ;
EGYPTIAN  : 'Egyptian' ;
GREEK     : 'Greek' ;
ROMAN     : 'Roman' ;
CELTIC    : 'Celtic' ;
GERMANIC  : 'Germanic' ;
SQUARE    : 'Square' ;
PEASANT   : 'Peasant' ;

// Units
UNIT : 'mm' | 'cm' ;

// G13/G14: number
NUMBER : DIGIT+ ('.' DIGIT+)? ;
fragment DIGIT : [0-9] ;

// G15: string literal
STRING : '"' ~["\r\n]* '"' ;

// G12: identifier — must come AFTER all keywords
ID : [a-zA-Z_][a-zA-Z0-9_]* ;

// Punctuation
LBRACE   : '{' ;
RBRACE   : '}' ;
LBRACKET : '[' ;
RBRACKET : ']' ;
COLON    : ':' ;
COMMA    : ',' ;

// Whitespace & comments — skip
WS      : [ \t\r\n]+ -> skip ;
COMMENT : '//' ~[\r\n]* -> skip ;
