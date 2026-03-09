# Generated from SoleScript.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .SoleScriptParser import SoleScriptParser
else:
    from SoleScriptParser import SoleScriptParser

# This class defines a complete generic visitor for a parse tree produced by SoleScriptParser.

class SoleScriptVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SoleScriptParser#program.
    def visitProgram(self, ctx:SoleScriptParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#statement.
    def visitStatement(self, ctx:SoleScriptParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#foot_decl.
    def visitFoot_decl(self, ctx:SoleScriptParser.Foot_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#obs_decl.
    def visitObs_decl(self, ctx:SoleScriptParser.Obs_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#last_decl.
    def visitLast_decl(self, ctx:SoleScriptParser.Last_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#boot_decl.
    def visitBoot_decl(self, ctx:SoleScriptParser.Boot_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#export_decl.
    def visitExport_decl(self, ctx:SoleScriptParser.Export_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#attr_list.
    def visitAttr_list(self, ctx:SoleScriptParser.Attr_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#attr_entry.
    def visitAttr_entry(self, ctx:SoleScriptParser.Attr_entryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#comp_list.
    def visitComp_list(self, ctx:SoleScriptParser.Comp_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#comp_entry.
    def visitComp_entry(self, ctx:SoleScriptParser.Comp_entryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#shoe_comp.
    def visitShoe_comp(self, ctx:SoleScriptParser.Shoe_compContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#dimensionValue.
    def visitDimensionValue(self, ctx:SoleScriptParser.DimensionValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#idValue.
    def visitIdValue(self, ctx:SoleScriptParser.IdValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#stringListValue.
    def visitStringListValue(self, ctx:SoleScriptParser.StringListValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#keywordValue.
    def visitKeywordValue(self, ctx:SoleScriptParser.KeywordValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#id.
    def visitId(self, ctx:SoleScriptParser.IdContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#number.
    def visitNumber(self, ctx:SoleScriptParser.NumberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#string_val.
    def visitString_val(self, ctx:SoleScriptParser.String_valContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SoleScriptParser#keyword_val.
    def visitKeyword_val(self, ctx:SoleScriptParser.Keyword_valContext):
        return self.visitChildren(ctx)



del SoleScriptParser