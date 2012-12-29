#!/usr/bin/python3 -tt

# Copyright 2012 Jussi Pakkanen

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import interpreter, environment
import os, stat

class ShellGenerator():
    
    def __init__(self, code, source_dir, build_dir):
        self.code = code
        self.environment = environment.Environment(source_dir, build_dir)
        self.interpreter = interpreter.Interpreter(code)
        self.build_filename = 'compile.sh'
    
    def generate(self):
        self.interpreter.run()
        outfilename = os.path.join(self.environment.get_build_dir(), self.build_filename)
        outfile = open(outfilename, 'w')
        outfile.write('#!/bin/sh\n')
        self.generate_commands(outfile)
        outfile.close()
        os.chmod(outfilename, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC |\
                 stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    def generate_single_compile(self, outfile, src):
        compiler = None
        for i in self.interpreter.compilers:
            if i.can_compile(src):
                compiler = i
                break
        if compiler is None:
            raise RuntimeError('No specified compiler can handle file ' + src)
        abs_src = os.path.join(self.environment.get_source_dir(), src)
        abs_obj = os.path.join(self.environment.get_build_dir(), src)
        abs_obj += '.' + self.environment.get_object_suffix()
        commands = compiler.get_exelist()
        commands += compiler.get_debug_flags()
        commands += compiler.get_std_warn_flags()
        commands += compiler.get_compile_only_flags()
        commands.append(abs_src)
        commands += compiler.get_output_flags()
        commands.append(abs_obj)
        quoted = environment.shell_quote(commands) + ['\n']
        outfile.write(' '.join(quoted))
        return abs_obj

    def generate_exe_link(self, outfile, outname, obj_list):
        outfile.write('Linking %s with files %s.\n' % (outname, ' '.join(obj_list)))

    def generate_commands(self, outfile):
        for i in self.interpreter.get_executables().items():
            name = i[0]
            e = i[1]
            print('Generating executable', name)
            outname = os.path.join(self.environment.get_build_dir(), e.get_basename())
            suffix = self.environment.get_exe_suffix()
            if suffix != '':
                outname = outname + '.' + suffix
            obj_list = []
            for src in e.get_sources():
                obj_list.append(self.generate_single_compile(outfile, src))
            self.generate_exe_link(outfile, outname, obj_list)

if __name__ == '__main__':
    code = """
    project('simple generator')
    language('c')
    executable('prog', 'prog.c')
    """
    os.chdir(os.path.split(__file__)[0])
    g = ShellGenerator(code, '.', 'test build area')
    g.generate()
