# AGENTS.md

Engineering principles for any agent working in my projects. These override
default habits.

## Do not preserve backward compatibility

Remove obsolete paths instead of adding compatibility layers, fallbacks, or
migrations. When something is replaced, the old thing goes away in the same
change. Dead code that "might still be used" is dead code.

## Choose the simplest implementation that fully meets the current requirements

Avoid speculative abstractions, configuration, and indirection. Solve the
requirement in front of you, completely — not a generalized version of it that
nobody asked for. A flag, a strategy interface, or a plugin point needs a
present-tense reason to exist.

## Grow the system in layers

Start from the smallest version that works end to end, and add each new
capability on top of a product that already works. Never trade a working
product for unfinished complexity. At every point in the work there should be
something that runs.

## Keep components modular and concerns clearly separated

Each module owns one concern and exposes a narrow surface. Boundaries are
decided deliberately, not discovered after the fact.

## Prefer established, well-maintained libraries

Use them when they reduce overall complexity or improve reliability. Do not
reimplement common functionality without a clear reason.

## Lean on the dependencies already in the project

Before writing your own implementation or adding a package, check what is
already installed. Do not assume a library lacks a capability without reading
its documentation and types first.

## Make architectural decisions for the long term

Do not accept a stopgap that only works for now and is meant to be replaced.
If the right shape is known, build the right shape. If it is not known yet,
say so and find out before committing the codebase to a direction.
