def output(grains):
    '''
    Output the grains in a clean way
    '''
    colors = salt.utils.get_colors(__opts__.get('color'))
    encoding = grains['locale_info']['defaultencoding']
    if encoding == 'unknown':
        encoding = 'utf-8'  # let's hope for the best

    ret = u''
    for id_, minion in grains.items():
        ret += u'{0}{1}{2}:\n'.format(colors['GREEN'], id_.decode(encoding), colors['ENDC'])
        for key in sorted(minion):
            ret += u'  {0}{1}{2}:'.format(colors['CYAN'], key.decode(encoding), colors['ENDC'])
            if key == 'cpu_flags':
                ret += colors['LIGHT_GREEN']
                for val in minion[key]:
                    ret += u' {0}'.format(val.decode(encoding))
                ret += '{0}\n'.format(colors['ENDC'])
            elif key == 'pythonversion':
                ret += ' {0}'.format(colors['LIGHT_GREEN'])
                for val in minion[key]:
                    ret += u'{0}.'.format(unicode(val))
                ret = ret[:-1]
                ret += '{0}\n'.format(colors['ENDC'])
            elif isinstance(minion[key], list):
                for val in minion[key]:
                    ret += u'\n      {0}{1}{2}'.format(colors['LIGHT_GREEN'], val.decode(encoding), colors['ENDC'])
                ret += '\n'
            else:
                ret += u' {0}{1}{2}\n'.format(colors['LIGHT_GREEN'], minion[key].decode(encoding), colors['ENDC'])
    return ret