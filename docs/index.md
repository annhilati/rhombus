---
icon: lucide/lightbulb
title: Introduction
---

Density function are Minecraft's way to describe, how terrain should look at a certain point.
Starting with 1.18.2, they are data driven, which means that terrain can be modified through a [datapack](https://minecraft.wiki/w/Data_pack), without the need to know how to program in Java. 

However, like many other things in datapacks, writing these is difficult due to the incomprehensible source format and the lack of good development environments.
In addition, the difficulty of density functions goes beyond mere development know-how and also requires a high degree of mathematical background knowledge and creativity — similar to the development of shaders.

*Rhombus* is a tool that facilitates some of these aspects, primarily designed to speed up the work process when you already know what you are doing.

!!! info "Beet Interoperability"
    If you already worked with development environments for datapacks, you might be pleased to hear that Rhombus is working hand in hand with [Beet](https://github.com/mcbeet/beet).
    Rhombus can be used without it, but the features that provide a real speed advantage are based on it.

<h2>What do I need to get started?</h2>

To use Rhombus efficiently, the following is recommended:

- A basic understanding of how to use Python and object oriented programming
- A basic understanding of how to use Python modules
- A basic understanding of how to use [Beet](https://github.com/mcbeet/beet)
- A basic understanding of how datapacks work

To see how Rhombus can be integrated into your workflow, see [Worfklow](workflow.md).