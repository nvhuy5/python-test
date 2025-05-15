from template_processors.template_processor import TemplateProcessor


class POFileProcessorRegistry:
    processors = {
        ".pdf": TemplateProcessor.PDF_0C_RL_H75_K0,
        ".txt": TemplateProcessor.TXT_PO202404007116,
        ".xlsx": TemplateProcessor.EXCELTEMPLATE,
        ".xls": TemplateProcessor.EXCELTEMPLATE,
    }

    @classmethod
    def get(cls, extension):
        return cls.processors.get(extension, None)


class MasterdataProcessorRegistry:
    processors = {
        ".txt": TemplateProcessor.TXT_MASTERADATA_TEMPLATE,
    }

    @classmethod
    def get(cls, extension):
        return cls.processors.get(extension, None)
