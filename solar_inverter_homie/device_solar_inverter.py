import logging

from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from homie.node.property.property_float import Property_Float
from homie.node.property.property_integer import Property_Integer
from homie.node.property.property_boolean import Property_Boolean

logger = logging.getLogger(__name__)

class Device_Solar_Inverter(Device_Base):
	def __init__(
		self, device_id=None, name=None, homie_settings=None, mqtt_settings=None
	):

		super().__init__(device_id, name, homie_settings, mqtt_settings)

		# Add the 3 nodes (power, energy, status) here
		node = Node_Base(self, id='power', name='Power', type_='Current power flow data')
		self.add_node(node)
		node.add_property(Property_Float(node, name='pv_voltage1', id='pv1', unit='V', settable=False))
		node.add_property(Property_Float(node, name='pv_voltage2', id='pv2', unit='V', settable=False))
		node.add_property(Property_Float(node, name='pv_voltage3', id='pv3', unit='V', settable=False))
		node.add_property(Property_Float(node, name='pv_current1', id='pi1', unit='A', settable=False))
		node.add_property(Property_Float(node, name='pv_current2', id='pi2', unit='A', settable=False))
		node.add_property(Property_Float(node, name='pv_current3', id='pi3', unit='A', settable=False))
		node.add_property(Property_Float(node, name='ac_voltage1', id='av1', unit='V', settable=False))
		node.add_property(Property_Float(node, name='ac_voltage2', id='av2', unit='V', settable=False))
		node.add_property(Property_Float(node, name='ac_voltage3', id='av3', unit='V', settable=False))
		node.add_property(Property_Float(node, name='ac_current1', id='ai1', unit='A', settable=False))
		node.add_property(Property_Float(node, name='ac_current2', id='ai2', unit='A', settable=False))
		node.add_property(Property_Float(node, name='ac_current3', id='ai3', unit='A', settable=False))
		node.add_property(Property_Float(node, name='ac_freq1', id='af1', unit='Hz', settable=False))
		node.add_property(Property_Float(node, name='ac_freq2', id='af2', unit='Hz', settable=False))
		node.add_property(Property_Float(node, name='ac_freq3', id='af3', unit='Hz', settable=False))

		node = Node_Base(self, id='energy', name='Energy', type_='Summarised energy data')
		self.add_node(node)
		node.add_property(Property_Integer(node, name='total', id='total', unit='kWh', settable=False))
		node.add_property(Property_Float(node, name='today', id='today', unit='kWh', settable=False))
		node.add_property(Property_Integer(node, name='now', id='now', unit='W', settable=False))

		node = Node_Base(self, id='status', name='Status', type_='Current status')
		self.add_node(node)
		node.add_property(Property_Boolean(node, name='online', id='online', settable=False))

		self.start()

	def update_pv_voltage(self, pv_v_array, pv_c_array, ac_v_array, ac_c_array, ac_f_array):
		power_node = self.get_node('power')

		for id, pv_line_val in enumerate(pv_v_array, start=1):
			prop_id = 'pv{}'.format(id)
			power_node.get_property(prop_id).value = pv_line_val
		for id, pv_line_val in enumerate(pv_c_array, start=1):
			prop_id = 'pi{}'.format(id)
			power_node.get_property(prop_id).value = pv_line_val
		for id, ac_line_val in enumerate(ac_v_array, start=1):
			prop_id = 'av{}'.format(id)
			power_node.get_property(prop_id).value = ac_line_val
		for id, ac_line_val in enumerate(ac_v_array, start=1):
			prop_id = 'ai{}'.format(id)
			power_node.get_property(prop_id).value = ac_line_val
		for id, ac_line_val in enumerate(ac_f_array, start=1):
			prop_id = 'af{}'.format(id)
			power_node.get_property(prop_id).value = ac_line_val

	def update_energy(self, total, today, now):
		energy_node = self.get_node('energy')

		energy_node.get_property('total').value = total;
		energy_node.get_property('today').value = today;
		energy_node.get_property('now').value = now;

	def update_status(self, status):
		self.get_node('status').get_property('online').value = status

# END OF FILE
