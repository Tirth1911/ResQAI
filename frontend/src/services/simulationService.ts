import { API_BASE_URL } from '@/lib/constants';
import { SimulationStatus, StartSimulationPayload } from '@/types';

class SimulationService {
  private baseUrl = `${API_BASE_URL}/simulation`;

  async getStatus(): Promise<SimulationStatus> {
    const res = await fetch(`${this.baseUrl}/status`, {
      cache: 'no-store',
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch simulation status: ${res.statusText}`);
    }
    return res.json();
  }

  async start(payload?: StartSimulationPayload): Promise<{ status: string; simulation: SimulationStatus }> {
    const res = await fetch(`${this.baseUrl}/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) {
      throw new Error(`Failed to start simulation: ${res.statusText}`);
    }
    return res.json();
  }

  async stop(): Promise<{ status: string; simulation: SimulationStatus }> {
    const res = await fetch(`${this.baseUrl}/stop`, {
      method: 'POST',
    });
    if (!res.ok) {
      throw new Error(`Failed to stop simulation: ${res.statusText}`);
    }
    return res.json();
  }

  async reset(): Promise<{ status: string; simulation: SimulationStatus }> {
    const res = await fetch(`${this.baseUrl}/reset`, {
      method: 'POST',
    });
    if (!res.ok) {
      throw new Error(`Failed to reset simulation: ${res.statusText}`);
    }
    return res.json();
  }

  async getSimulationStatus(): Promise<SimulationStatus> {
    return this.getStatus();
  }

  async startSimulation(payload?: StartSimulationPayload): Promise<SimulationStatus> {
    const res = await this.start(payload);
    return res.simulation || (res as any);
  }

  async stopSimulation(): Promise<SimulationStatus> {
    const res = await this.stop();
    return res.simulation || (res as any);
  }

  async resetSimulation(): Promise<SimulationStatus> {
    const res = await this.reset();
    return res.simulation || (res as any);
  }

  async triggerSingle(
    scenarioIndex: number = 0,
    duplicateSimulation: boolean = true
  ): Promise<{ status: string; scenario_title: string; simulation: SimulationStatus }> {
    const res = await fetch(
      `${this.baseUrl}/trigger?scenario_index=${scenarioIndex}&duplicate_simulation=${duplicateSimulation}`,
      {
        method: 'POST',
      }
    );
    if (!res.ok) {
      throw new Error(`Failed to trigger scenario: ${res.statusText}`);
    }
    return res.json();
  }

  async setupDemo(): Promise<{ status: string; message: string; demo_incident_id: string }> {
    const res = await fetch(`${this.baseUrl}/demo/setup`, {
      method: 'POST',
    });
    if (!res.ok) {
      throw new Error(`Failed to setup demo environment: ${res.statusText}`);
    }
    return res.json();
  }

  async executeDemoStep(stepNumber: number): Promise<{
    step: number;
    step_title: string;
    description: string;
    data: any;
  }> {
    const res = await fetch(`${this.baseUrl}/demo/step/${stepNumber}`, {
      method: 'POST',
    });
    if (!res.ok) {
      throw new Error(`Failed to execute demo step ${stepNumber}: ${res.statusText}`);
    }
    return res.json();
  }
}

export const simulationService = new SimulationService();
