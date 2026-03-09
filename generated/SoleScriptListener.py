# Generated from SoleScript.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .SoleScriptParser import SoleScriptParser
else:
    from SoleScriptParser import SoleScriptParser

# This class defines a complete listener for a parse tree produced by SoleScriptParser.
class SoleScriptListener(ParseTreeListener):

    # Enter a parse tree produced by SoleScriptParser#program.
    def enterProgram(self, ctx:SoleScriptParser.ProgramContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#program.
    def exitProgram(self, ctx:SoleScriptParser.ProgramContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#statement.
    def enterStatement(self, ctx:SoleScriptParser.StatementContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#statement.
    def exitStatement(self, ctx:SoleScriptParser.StatementContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#foot_decl.
    def enterFoot_decl(self, ctx:SoleScriptParser.Foot_declContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#foot_decl.
    def exitFoot_decl(self, ctx:SoleScriptParser.Foot_declContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#obs_decl.
    def enterObs_decl(self, ctx:SoleScriptParser.Obs_declContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#obs_decl.
    def exitObs_decl(self, ctx:SoleScriptParser.Obs_declContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#last_decl.
    def enterLast_decl(self, ctx:SoleScriptParser.Last_declContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#last_decl.
    def exitLast_decl(self, ctx:SoleScriptParser.Last_declContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#boot_decl.
    def enterBoot_decl(self, ctx:SoleScriptParser.Boot_declContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#boot_decl.
    def exitBoot_decl(self, ctx:SoleScriptParser.Boot_declContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#export_decl.
    def enterExport_decl(self, ctx:SoleScriptParser.Export_declContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#export_decl.
    def exitExport_decl(self, ctx:SoleScriptParser.Export_declContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#attr_list.
    def enterAttr_list(self, ctx:SoleScriptParser.Attr_listContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#attr_list.
    def exitAttr_list(self, ctx:SoleScriptParser.Attr_listContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#attr_entry.
    def enterAttr_entry(self, ctx:SoleScriptParser.Attr_entryContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#attr_entry.
    def exitAttr_entry(self, ctx:SoleScriptParser.Attr_entryContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#comp_list.
    def enterComp_list(self, ctx:SoleScriptParser.Comp_listContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#comp_list.
    def exitComp_list(self, ctx:SoleScriptParser.Comp_listContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#comp_entry.
    def enterComp_entry(self, ctx:SoleScriptParser.Comp_entryContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#comp_entry.
    def exitComp_entry(self, ctx:SoleScriptParser.Comp_entryContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#shoe_comp.
    def enterShoe_comp(self, ctx:SoleScriptParser.Shoe_compContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#shoe_comp.
    def exitShoe_comp(self, ctx:SoleScriptParser.Shoe_compContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#dimensionValue.
    def enterDimensionValue(self, ctx:SoleScriptParser.DimensionValueContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#dimensionValue.
    def exitDimensionValue(self, ctx:SoleScriptParser.DimensionValueContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#idValue.
    def enterIdValue(self, ctx:SoleScriptParser.IdValueContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#idValue.
    def exitIdValue(self, ctx:SoleScriptParser.IdValueContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#stringListValue.
    def enterStringListValue(self, ctx:SoleScriptParser.StringListValueContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#stringListValue.
    def exitStringListValue(self, ctx:SoleScriptParser.StringListValueContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#keywordValue.
    def enterKeywordValue(self, ctx:SoleScriptParser.KeywordValueContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#keywordValue.
    def exitKeywordValue(self, ctx:SoleScriptParser.KeywordValueContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#id.
    def enterId(self, ctx:SoleScriptParser.IdContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#id.
    def exitId(self, ctx:SoleScriptParser.IdContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#number.
    def enterNumber(self, ctx:SoleScriptParser.NumberContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#number.
    def exitNumber(self, ctx:SoleScriptParser.NumberContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#string_val.
    def enterString_val(self, ctx:SoleScriptParser.String_valContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#string_val.
    def exitString_val(self, ctx:SoleScriptParser.String_valContext):
        pass


    # Enter a parse tree produced by SoleScriptParser#keyword_val.
    def enterKeyword_val(self, ctx:SoleScriptParser.Keyword_valContext):
        pass

    # Exit a parse tree produced by SoleScriptParser#keyword_val.
    def exitKeyword_val(self, ctx:SoleScriptParser.Keyword_valContext):
        pass



del SoleScriptParser