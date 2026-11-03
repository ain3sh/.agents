/*
 * Stageshow kit, from https://github.com/benjitaylor/skills (stageshow/).
 *
 * MIT License
 *
 * Copyright (c) 2026 Benji Taylor
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
// Components import their own CSS, so no separate style import is required.
// Which unused styles are removed depends on the host bundler.
// kit/stageshow.css explicitly loads every kit style up front.

// The stage: the canvas, the script, the cursor, measuring and playback
export { Stage } from './stage'
export { useLook } from './looks'
export { useReducedMotion } from './reduced-motion'
export { inset, box, between, contains } from './measure'
export type { StageProps, Play, LookTokens } from './stage'
export type { Act, Script } from './act'
export type { Point, Rect, Target } from './measure'
export type { CursorKind, CursorStyle } from './cursor'
export type { Theme, Palette, Fidelity, Layout } from './looks'
export type { KeysAt } from './keys'
export { clock, installVirtualClock } from './clock'
export type { ClockControl } from './clock'

// Frames: windows, devices and system surfaces, from real geometry
export { Window, Bar, Text, Prompt, Caret } from './window'
export type { WindowProps, BarProps, TextProps, PromptProps } from './window'
export { Phone, LockScreen, Notification, WALLPAPER } from './phone'
export type { PhoneProps, PhoneFrame, LockScreenProps, NotificationProps } from './phone'
export { Keyboard } from './ios'
export type { KeyboardProps } from './ios'
export { Thread, Bubble, Stamp, Receipt } from './messages'
export type { ThreadProps, BubbleProps } from './messages'

// Motion: behaviors that have to hold up frame by frame (motion/, one file per part)
export { Connector, Count, Roll, Swap, Collapse, Fly, Follow, cellOf, States, Stream, Popover, Camera, Scroll, Expand } from './motion'
export type { ConnectorProps, CountProps, FollowProps, FlyProps, PopoverOrigin } from './motion'
export { EASE, bezier, css as easeCss } from './ease'
export type { EaseName, Bezier } from './ease'

// Small parts: starting points with quiet defaults; restyle them as the product does (parts/, controls/)
export { Avatar, Check, Icon, Spinner, Toast, Tooltip, Meter, Menu, Facepile, Chip, BrandMark, Pin, Row } from './parts'
export type { AvatarProps, IconName, BrandMarkProps, PinProps, RowProps } from './parts'
export { brandMarks } from './brands'
export type { BrandName, BrandAsset } from './brands'
export { Field, Segmented, Toggle, Tabs, Badge, Slot } from './controls'
export type { FieldProps } from './controls'
export { Code } from './code'
export type { CodeLine } from './code'
export { Chart, chartPoints } from './chart'
export type { ChartProps } from './chart'
