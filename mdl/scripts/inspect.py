"""Inspect mdl definitions"""
from __future__ import print_function

import argparse
import textwrap

from . import bootstrap
from .. import interfaces

grpAppTitle = textwrap.TextWrapper(
    initial_indent='* ',
    subsequent_indent='  ')

grpRouteTitle = textwrap.TextWrapper(
    initial_indent='  - ',
    subsequent_indent='    ')

grpRouteBody = textwrap.TextWrapper(
    initial_indent='    ',
    subsequent_indent='      ')


def main():  # pragma: no cover
    args = InspectCommand.parser.parse_args()

    config = bootstrap(args.config)
    registry = config.commit()

    registry.install()

    cmd = InspectCommand(args, registry)
    cmd.run()

    registry.uninstall()


class InspectCommand(object):  # pragma: no cover

    parser = argparse.ArgumentParser(description='mdl inspect')
    parser.add_argument('config', metavar='config',
                        help='yaml config file')

    def __init__(self, args, registry):
        self.options = args
        self.registry = registry

    def run(self):
        for name, app in self.registry.getUtilitiesFor(
                interfaces.IApplication):
            self.process_app(app)

        print('')

    def process_app(self, app):
        print('')
        print(grpAppTitle.fill(app.name))

        wrp = textwrap.TextWrapper(
            initial_indent=' '*4, subsequent_indent=' '*4, width=300)
        for key, value in app.options.items():
            print(wrp.fill('%s: %s' % (key, value)))

        self.process_routes(app)

    def process_routes(self, app):
        for route in app.routes():
            print('')
            print(grpRouteTitle.fill(
                '%s: %s %s' % (
                    route.name, route.options.get('path'),
                    list(route.options.get('methods')))))
            print(grpRouteBody.fill('transform:'))
            self.process_transform(route.transform, 6)

    def process_transform(self, transform, level=0):
        defs = interfaces.ITransformDefinition(transform, None)
        wrp = textwrap.TextWrapper(
            initial_indent=' '*level,
            subsequent_indent=' '*(level+4), width=300)
        wrp2 = textwrap.TextWrapper(
            initial_indent=' '*(level+2),
            subsequent_indent=' '*(level+4), width=300)

        if defs is not None:
            print('')
            if defs.in_model:
                print(wrp.fill('input: %r' % defs.in_model))
            else:
                print(wrp.fill('output: UNKNOWN', ))

            if defs.name:
                print(wrp2.fill('name: %s (%s)' % (defs.name, defs.func)))
            if defs.description:
                for line in defs.description.split('\n'):
                    print(wrp2.fill('%s' % line))

        insp = interfaces.IInspectable(transform, None)
        if insp is not None:
            l = level if defs is None else level + 2
            for tr in insp.transforms():
                self.process_transform(tr, l)

        if defs:
            if defs.out_model:
                print(wrp.fill('output: %s' % defs.out_model))
            else:
                print(wrp.fill('output: UNKNOWN'))
