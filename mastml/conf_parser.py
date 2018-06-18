from configobj import ConfigObj
from distutils.util import strtobool
from . import metrics
from .legos.model_finder import check_models_mixed

def parse_conf_file(filepath):
        "Accepts the filepath of a conf file and returns its parsed dictionary"

        conf = ConfigObj(filepath)

        required_sections = ['GeneralSetup', 'DataSplits', 'Models']
        feature_sections = ['FeatureNormalization', 'FeatureGeneration', 'FeatureSelection']
        feature_section_dicts = [conf[name] for name in feature_sections if name in conf]
        all_sections = required_sections + feature_sections

        # Are all required sections present in the file?
        for name in required_sections:
            if name not in conf:
                raise Exception(f"Missing required section: [{name}]")

        # Are there any invalid sections?
        for section_name in conf:
            if section_name not in all_sections:
                raise Exception(f'[{section_name}] is not a valid section! Valid sections: {all_sections}')

        # Does a subsection-only section contain a parameter?
        dict_dicts = [conf, conf['DataSplits'], conf['Models']] + feature_section_dicts
        for dictionary in dict_dicts:
            for name,value in dictionary.items():
                if not isinstance(value, dict):
                    raise TypeError(f"Parameter in subsection-only section: {name}={value}")

        # Collect all subsections which contain only parameters (no subsubsections):
        parameter_dicts = [conf['GeneralSetup']] + conf['Models'].values() + conf['DataSplits'].values()
        for feature_section in feature_section_dicts:
            parameter_dicts.extend(feature_section.values())

        # Do any parameter sections contain a subsection?
        # Also, cast the strings to their respective types
        for parameter_dict in parameter_dicts:
            for name, value in parameter_dict.items():
                if isinstance(value, dict):
                    raise TypeError(f"Subsection in parameter-only section: {key}")
                parameter_dict[name] = _fix_types(value)

        # Ensure all models are either classifiers or regressors: (raises error if mixed)
        is_classification = conf['is_classification'] = check_models_mixed(conf['Models'].keys())

        ## Assign default values to unspecified or 'Auto' options: ##

        for name in feature_sections:
            if name not in conf or conf[name] == dict():
                conf[name] = {'DoNothing': {}}

        for name in ['input_features', 'target_feature']:
            if (name not in conf['GeneralSetup']) or (conf['GeneralSetup'][name] == 'Auto'):
                conf['GeneralSetup'][name] = None

        if 'metrics' in conf['GeneralSetup']:
            conf['metrics'] = conf['GeneralSetup']['metrics']
            del conf['GeneralSetup']['metrics']
        if 'metrics' not in conf or conf['metrics'] == 'Auto':
            if is_classification:
                conf['metrics'] = ['accuracy_score', 'precision_score', 'recall_score']
            else:
                conf['metrics'] = ['r2_score', 'explained_variance_score']
        else: # User has specified their own specific metrics:
            metrics.check_names(conf['metrics'], is_classification)

        # TODO Grouping is not a real section, figure out how that would really work
        #if 'grouping_feature' in conf['Grouping']:
        #    conf['GeneralSetup']['grouping_feature'] = conf['Grouping']['grouping_feature']

        return conf

def _fix_types(maybe_list):
    " Takes user parameter string and gives true value "

    if isinstance(maybe_list, list):
        return [fix_types(item) for item in maybe_list]

    try: return strtobool(maybe_list)
    except ValueError: pass

    try: return int(maybe_list)
    except ValueError: pass

    try: return float(maybe_list)
    except ValueError: pass

    return str(maybe_list)