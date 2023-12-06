#####
# Copyright (c) 2011-2012, NVIDIA Corporation.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the NVIDIA Corporation nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
#####


import datetime
import multiprocessing

import psutil
import pynvml
from cpuinfo import get_cpu_info

cpu_info = get_cpu_info()
try:
    CPU_NAME = cpu_info["brand"]
except KeyError:
    CPU_NAME = cpu_info["brand_raw"]

CPU_COUNT = multiprocessing.cpu_count()
CPU_NAME = f"{CPU_NAME} ({CPU_COUNT} cores)"


def handleError(err):
    #
    # Converts errors into string messages
    #
    if err.value == pynvml.NVML_ERROR_NOT_SUPPORTED:
        return "N/A"
    else:
        return err.__str__()


#######


def DeviceQuery():
    result = {"timestap": str(datetime.date.today()), "attached_gpus": []}
    try:
        #
        # Initialize NVML
        #
        pynvml.nvmlInit()

        result["driver_version"] = pynvml.nvmlSystemGetDriverVersion().decode("utf-8")

        deviceCount = pynvml.nvmlDeviceGetCount()

        for i in range(0, deviceCount):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)

            pciInfo = pynvml.nvmlDeviceGetPciInfo(handle)
            tempres = {}
            result["attached_gpus"].append(tempres)
            tempres["id"] = i
            tempres["PCI bus id"] = pciInfo.busId.decode("utf-8")

            tempres["product_name"] = pynvml.nvmlDeviceGetName(handle).decode("utf-8")

            try:
                uuid = pynvml.nvmlDeviceGetUUID(handle)
            except pynvml.NVMLError as err:
                uuid = handleError(err)

            tempres["uuid"] = uuid.decode("utf-8")

            try:
                vbios = pynvml.nvmlDeviceGetVbiosVersion(handle).decode("utf-8")
            except pynvml.NVMLError as err:
                vbios = handleError(err)

            tempres["vbios_version"] = vbios

            pci = {}
            tempres["pci"] = pci
            pci["bus"] = pciInfo.bus
            pci["device"] = pciInfo.device
            pci["domain"] = pciInfo.domain
            pci["device_id"] = pciInfo.pciDeviceId
            pci["bus_id"] = pciInfo.busId.decode("utf-8")
            pci["sub_system_id"] = pciInfo.pciSubSystemId

            linkInfo = {}
            pci["link_info"] = linkInfo

            try:
                gen = pynvml.nvmlDeviceGetMaxPcieLinkGeneration(handle)
            except pynvml.NVMLError as err:
                gen = handleError(err)

            linkInfo["max_link_gen"] = gen

            try:
                gen = pynvml.nvmlDeviceGetCurrPcieLinkGeneration(handle)
            except pynvml.NVMLError as err:
                gen = handleError(err)

            linkInfo["current_link_gen"] = gen

            try:
                width = pynvml.nvmlDeviceGetMaxPcieLinkWidth(handle)
            except pynvml.NVMLError as err:
                width = handleError(err)

            linkInfo["max_link_width"] = width

            try:
                width = pynvml.nvmlDeviceGetCurrPcieLinkWidth(handle)
            except pynvml.NVMLError as err:
                width = handleError(err)

            linkInfo["current_link_width"] = width

            try:
                fan = pynvml.nvmlDeviceGetFanSpeed(handle)
            except pynvml.NVMLError as err:
                fan = handleError(err)
            tempres["fan_speed"] = fan

            try:
                perfState = pynvml.nvmlDeviceGetPowerState(handle)
                perfStateStr = f"P{perfState}"
            except pynvml.NVMLError as err:
                perfStateStr = handleError(err)
            tempres["performance_state"] = perfStateStr

            try:
                memInfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
                mem_total = memInfo.total / 1024 / 1024
                mem_used = memInfo.used / 1024 / 1024
                mem_free = memInfo.total / 1024 / 1024 - memInfo.used / 1024 / 1024
            except pynvml.NVMLError as err:
                error = handleError(err)
                mem_total = error
                mem_used = error
                mem_free = error

            tempres["total_memory"] = mem_total
            tempres["used_memory"] = mem_used
            tempres["free_memory"] = mem_free

            try:
                mode = pynvml.nvmlDeviceGetComputeMode(handle)
                if mode == pynvml.NVML_COMPUTEMODE_DEFAULT:
                    modeStr = "Default"
                elif mode == pynvml.NVML_COMPUTEMODE_EXCLUSIVE_THREAD:
                    modeStr = "Exclusive Thread"
                elif mode == pynvml.NVML_COMPUTEMODE_PROHIBITED:
                    modeStr = "Prohibited"
                elif mode == pynvml.NVML_COMPUTEMODE_EXCLUSIVE_PROCESS:
                    modeStr = "Exclusive Process"
                else:
                    modeStr = "Unknown"
            except pynvml.NVMLError as err:
                modeStr = handleError(err)

            tempres["compute_mode"] = modeStr

            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = util.gpu
                mem_util = util.memory
            except pynvml.NVMLError as err:
                error = handleError(err)
                gpu_util = error
                mem_util = error
            utilization = {}
            tempres["utilization"] = utilization

            utilization["gpu"] = gpu_util
            utilization["mem"] = mem_util

            try:
                temp = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU
                )
            except pynvml.NVMLError as err:
                temp = handleError(err)

            tempres["temperature"] = temp

            try:
                graphics = pynvml.nvmlDeviceGetClockInfo(
                    handle, pynvml.NVML_CLOCK_GRAPHICS
                )
            except pynvml.NVMLError as err:
                graphics = handleError(err)
            tempres["graphics_clock"] = graphics
            try:
                sm = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
            except pynvml.NVMLError as err:
                sm = handleError(err)

            tempres["sm_clock"] = sm
            try:
                mem = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            except pynvml.NVMLError as err:
                mem = handleError(err)

            tempres["mem_clock"] = mem

            try:
                graphics = pynvml.nvmlDeviceGetMaxClockInfo(
                    handle, pynvml.NVML_CLOCK_GRAPHICS
                )
            except pynvml.NVMLError as err:
                graphics = handleError(err)

            tempres["graphics_max_clock"] = graphics

            try:
                sm = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_SM)
            except pynvml.NVMLError as err:
                sm = handleError(err)
            tempres["sm_max_clock"] = sm
            try:
                mem = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            except pynvml.NVMLError as err:
                mem = handleError(err)

            tempres["mem_max_clock"] = mem
            gpu_procs = {}
            tempres["processes"] = gpu_procs
            try:
                procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                graphics = pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle)

                for p in procs + graphics:
                    try:
                        # discard the options used for the process
                        # to avoid a long string
                        name = (
                            pynvml.nvmlSystemGetProcessName(p.pid)
                            .decode("utf-8")
                            .split(" ")[0]
                        )
                    except pynvml.NVMLError as err:
                        if err.value == pynvml.NVML_ERROR_NOT_FOUND:
                            # probably went away
                            continue
                        else:
                            name = handleError(err)

                    gpu_procs[p.pid] = {}

                    gpu_procs[p.pid]["process_name"] = name

                    if p.usedGpuMemory is None:
                        mem = "N\\A"
                    else:
                        mem = p.usedGpuMemory / 1024 / 1024
                    gpu_procs[p.pid]["used_memory"] = mem

            except pynvml.NVMLError:
                pass

    except pynvml.NVMLError:
        pass

    try:
        pynvml.nvmlShutdown()
    except pynvml.NVMLError:
        pass

    cpu_stat = {}
    cpu_stat["name"] = CPU_NAME
    cpu_stat["usage"] = psutil.cpu_percent()

    vmem = psutil.virtual_memory()
    ram_stat = {
        "total": vmem.total / (1024**3),
        "used": vmem.used / (1024**3),
        "usage": vmem.percent,
    }

    result["cpu"] = cpu_stat
    result["ram"] = ram_stat

    return result
