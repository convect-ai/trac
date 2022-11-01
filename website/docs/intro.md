---
sidebar_position: 1
sidebar_label: What is TRAC?
---

# TRAC Introduction

## What is TRAC

TRAC stands for The Runner for Application as Containers. It packages a locally developed Data Science solution (either in the form of scripts or notebooks) in a container and converts it into an interactive application.

### What problem does it solve

TRAC solves the following problem for Data Scientists/Anlysts and engineers who are developing data-driven solutions:

> I have a working `main.py`, then what?

Normally, one will work with Frontend and Backend engineers to convert the local script into a callable web service, develop an UI so stakeholders play around with the soluton, and deploy the application to a hosting platform.
This apparently requires lots of skills in various fields. It's hard to do all the things in a "Fullstack" way.

TRAC eases the process by letting Data Scientists/Analysts focus on what it matters -- developing the core data science solution. It handles the rest -- UI, data management, deployment on behalf of an application author. So you can quickly make your solution "usable" by stakehodlers and make impacts.



## Features

- Automatically generates UI for your application.
- Automatically generates API for your application.
- Automatically manages backend deployments for your application.
- Your application data can live in multiple backends, including Google Sheets, Microsoft Excel, and managed Database, so you can share them easily with stakeholders.
- Helps you manage datasets and experiements for your application.


## Usage

On the high level, to publish a TRAC app, you need the following steps.
1. Develop your data science solution locally, either in the form of scripts or notebooks. Make sure it runs smoothly on your local machine.
2. Declare the datasets and their formats your solution requires and produces.
3. Declare the configurations your solution is able to handle.
4. Build an application image.
5. Publish the image to TRAC platform.
6. Send the published URL to stakeholders so they can start to use your application.

You can view a [concrete example](docs/tutorial-vrp/01-develop-locally.md) on how to publish a Vehicle Routing application for fleet management operations.
