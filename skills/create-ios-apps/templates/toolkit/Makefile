APP_NAME := __APP_NAME__
APP_SCHEME ?= __APP_NAME__
APP_PLATFORM := __PLATFORM__
CONFIGURATION ?= Debug
SIM_NAME ?= __SIM_NAME__

WORKSPACE := $(firstword $(wildcard *.xcworkspace))
PROJECT := $(firstword $(wildcard *.xcodeproj))
ifeq ($(strip $(PROJECT)),)
PROJECT := $(APP_NAME).xcodeproj
endif

ifeq ($(strip $(WORKSPACE)),)
BUILD_FILE_FLAG := -project $(PROJECT)
else
BUILD_FILE_FLAG := -workspace $(WORKSPACE)
endif

.DEFAULT_GOAL := build-and-run

DERIVED_DATA := build/DerivedData
LOG_DIR := build/logs

ifeq ($(APP_PLATFORM),ios)
BUILD_PRODUCTS := $(DERIVED_DATA)/Build/Products/$(CONFIGURATION)-iphonesimulator
else
BUILD_PRODUCTS := $(DERIVED_DATA)/Build/Products/$(CONFIGURATION)
DESTINATION := platform=macOS,arch=arm64
endif

APP_PATH := $(BUILD_PRODUCTS)/$(APP_SCHEME).app

STRICT_FLAGS := GCC_TREAT_WARNINGS_AS_ERRORS=YES \
	SWIFT_TREAT_WARNINGS_AS_ERRORS=YES \
	SWIFT_STRICT_CONCURRENCY=complete

.PHONY: help diagnose build test run build-and-run build-and-run-background clean

help:
	@printf "%s\n" \
		"Targets:" \
		"  make build                    Build with strict warnings" \
		"  make test                     Run unit tests" \
		"  make run                      Launch app (requires prior build)" \
		"  make build-and-run            Build then launch" \
		"  make build-and-run-background Build then launch in background" \
		"  make clean                    Remove build artifacts" \
		"  make diagnose                 Print toolchain + project info"

diagnose:
ifeq ($(APP_PLATFORM),ios)
	@APP_SCHEME="$(APP_SCHEME)" APP_PLATFORM="$(APP_PLATFORM)" \
		APP_DESTINATION="$$(scripts/resolve_sim_destination.sh --sim-name "$(SIM_NAME)" 2>/dev/null || echo unknown)" \
		PROJECT="$(PROJECT)" WORKSPACE="$(WORKSPACE)" \
		scripts/diagnose.sh
else
	@APP_SCHEME="$(APP_SCHEME)" APP_PLATFORM="$(APP_PLATFORM)" \
		APP_DESTINATION="$(DESTINATION)" \
		PROJECT="$(PROJECT)" WORKSPACE="$(WORKSPACE)" \
		scripts/diagnose.sh
endif

build:
ifeq ($(APP_PLATFORM),ios)
	@DESTINATION="$$(scripts/resolve_sim_destination.sh --sim-name "$(SIM_NAME)")"; \
	if [ -z "$$DESTINATION" ]; then echo "No iOS Simulator found."; exit 1; fi; \
	LOG_DIR="$(LOG_DIR)" scripts/xcbuild.sh --action build -- \
		$(BUILD_FILE_FLAG) -scheme $(APP_SCHEME) -configuration $(CONFIGURATION) \
		-destination "$$DESTINATION" -derivedDataPath $(DERIVED_DATA) \
		$(STRICT_FLAGS) build
else
	@LOG_DIR="$(LOG_DIR)" scripts/xcbuild.sh --action build -- \
		$(BUILD_FILE_FLAG) -scheme $(APP_SCHEME) -configuration $(CONFIGURATION) \
		-destination '$(DESTINATION)' -derivedDataPath $(DERIVED_DATA) \
		$(STRICT_FLAGS) build
endif

test:
ifeq ($(APP_PLATFORM),ios)
	@DESTINATION="$$(scripts/resolve_sim_destination.sh --sim-name "$(SIM_NAME)")"; \
	if [ -z "$$DESTINATION" ]; then echo "No iOS Simulator found."; exit 1; fi; \
	LOG_DIR="$(LOG_DIR)" scripts/xcbuild.sh --action test -- \
		$(BUILD_FILE_FLAG) -scheme $(APP_SCHEME) -configuration $(CONFIGURATION) \
		-destination "$$DESTINATION" -derivedDataPath $(DERIVED_DATA) \
		$(STRICT_FLAGS) test
else
	@LOG_DIR="$(LOG_DIR)" scripts/xcbuild.sh --action test -- \
		$(BUILD_FILE_FLAG) -scheme $(APP_SCHEME) -configuration $(CONFIGURATION) \
		-destination '$(DESTINATION)' -derivedDataPath $(DERIVED_DATA) \
		$(STRICT_FLAGS) test
endif

run:
ifeq ($(APP_PLATFORM),ios)
	@scripts/run_app_ios_sim.sh --app-path "$(APP_PATH)" --sim-name "$(SIM_NAME)"
else
	@scripts/run_app_macos.sh --app-path "$(APP_PATH)"
endif

build-and-run: build run

build-and-run-background: build
ifeq ($(APP_PLATFORM),ios)
	@scripts/run_app_ios_sim.sh --app-path "$(APP_PATH)" --sim-name "$(SIM_NAME)" --background
else
	@scripts/run_app_macos.sh --app-path "$(APP_PATH)" --background
endif

clean:
	@scripts/clean.sh
