"""Built-in analyzer plugins, one module per technology.

Each module exposes a module-level ``PLUGIN`` (an :class:`AnalyzerPlugin`). The
:class:`~devops_ai_toolkit.plugins.manager.PluginManager` discovers them by
iterating this package — adding a new built-in is just dropping in a new module.
Third-party plugins are discovered separately via entry points, so the same
mechanism scales to hundreds of plugins.
"""
